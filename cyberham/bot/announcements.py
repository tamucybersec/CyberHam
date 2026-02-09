from typing import Any, TypeAlias
from pytz import timezone

import discord
from discord import app_commands
from datetime import datetime as dt, timedelta, date
from calendar import day_name
from cyberham import guild_id, admin_permission
from cyberham.bot.bot import Bot
from cyberham.bot.utils import valid_guild
from cyberham.bot.constants import activity_group_channels
from cyberham.utils.date import to_central_time, format_central_time


Events: TypeAlias = dict[int, dict[str, list[discord.ScheduledEvent]]]


def setup_commands(bot: Bot):
    command_tree = bot.command_tree

    @app_commands.default_permissions(**admin_permission)
    @command_tree.command(
        name="generate_announcements",
        description="generates announcements boilerplate based on events",
        guilds=guild_id,
    )
    async def generate_announcements(interaction: discord.Interaction):
        if not await valid_guild(interaction):
            return
        assert interaction.guild is not None
        await interaction.response.defer(thinking=True)

        monday, friday = get_current_week_range()
        events: Events = initialize_event_dict()
        events_announced = 0

        for event in await interaction.guild.fetch_scheduled_events():
            start = to_central_time(event.start_time)
            if is_event_this_week(start, monday, friday):
                add_event_to_dict(events, event)
                events_announced += 1

        if events_announced == 0:
            await interaction.followup.send("No events for this week.")
        else:
            boilerplate = generate_event_markdown(events)
            await interaction.followup.send(boilerplate)

    # satisfy type checker
    _: list[Any] = [generate_announcements]


def get_current_week_range() -> tuple[date, date]:
    """Returns the start (Monday) and end (Friday) of the current week."""
    today = dt.today().date()
    if today.weekday() == 6:  # count Sunday as next week
        monday = today + timedelta(days=1)
    else:
        monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday


def initialize_event_dict() -> Events:
    """Prepares an empty dict for sorting events by weekday and location."""
    return {i: {} for i in range(5)}


def is_event_this_week(start: dt, monday: date, friday: date) -> bool:
    """Checks if the event falls within the current Monday-Friday range."""
    return monday <= start.date() <= friday


def add_event_to_dict(events: Events, event: discord.ScheduledEvent):
    """Adds an event to the appropriate place in the events dictionary."""
    start = event.start_time.astimezone(timezone("US/Central"))
    weekday = start.weekday()
    location = event.location or "TBD"
    if location not in events[weekday]:
        events[weekday][location] = []
    events[weekday][location].append(event)


def generate_event_markdown(events: Events) -> str:
    boilerplate = """
        # Howdy everyone! <:sunglasses_cowboy:916376081576116354>
        Here's what we have for this week
    """.strip()

    for weekday, locations in events.items():
        if not locations:
            continue

        boilerplate += f"\n## __{day_name[weekday]}__:\n"
        for location, scheduled_events in locations.items():
            map_link = get_map_link(location)
            boilerplate += f"**{location}**{map_link}\n"

            for event in scheduled_events:
                start = format_central_time(event.start_time)
                end = format_central_time(event.end_time) if event.end_time else "TBD"
                channel = get_activity_group_channel(
                    event.description if event.description else ""
                )
                boilerplate += (
                    f"- **{event.name}** | {channel}{start} - {end}\n"
                )

    return boilerplate


def get_map_link(location: str) -> str:
    building = location.split(" ")[0]
    if len(building) in [3, 4]:
        map_link = f" ([Map](<https://aggiemap.tamu.edu/map/d?bldg={building}>))"
    else:
        map_link = ""
    return map_link


def get_activity_group_channel(group: str) -> str:
    channel = ""
    for key, value in activity_group_channels.items():
        if key in group:
            channel = f"<#{value}> "
            break
    return channel
