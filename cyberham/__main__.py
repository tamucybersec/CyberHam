import logging
from typing import Literal
from pytz import timezone

import discord
from discord import app_commands, ui
from discord import EntityType
from discord import PrivacyLevel

from datetime import datetime as dt, timedelta
from calendar import day_name

import cyberham.backend as backend
from cyberham import guild_id, discord_token, admin_channel_id

"""
Define Bot Attributes
"""

logger = logging.getLogger(__name__)


class Bot(discord.Client):
    def __init__(self):
        super().__init__(
            intents=discord.Intents(
                guilds=True, members=True, messages=True, guild_scheduled_events=True
            )
        )
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        for g in guild_id:
            await reg.sync(guild=g)
            logger.info("synced server ", g.id)
        self.synced = True
        logger.info("bot online")

    async def on_scheduled_event_create(self, event):
        # voice channel events do not trigger this
        points = 50
        time = event.start_time.astimezone(timezone("US/Central"))

        code = backend.create_event(
            event.name, points, time.strftime("%m/%d/%Y"), "", str(event.creator_id)
        )
        embed = event_info(event.name, points, time.strftime("%m/%d/%Y"), code, "")
        await self.get_channel(admin_channel_id).send(
            f"The code is `{code}`", embed=embed
        )


client = Bot()

backend.init_db()
reg = app_commands.CommandTree(client)
"""
Discord Bot UI
"""


class PageDisplay(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.response = None
        self.page = 0

    @discord.ui.button(
        style=discord.ButtonStyle.primary, custom_id="el_left", emoji="◀"
    )
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        else:
            await interaction.response.defer()
            return

        embed = event_list_embed(self.page)
        if embed is None:
            await interaction.response.defer()
            return
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        style=discord.ButtonStyle.primary, custom_id="el_next", emoji="▶"
    )
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < backend.get_event_count() // 5:
            self.page += 1
        embed = event_list_embed(self.page)
        if embed is None:
            await interaction.response.defer()
            return
        await interaction.response.edit_message(embed=embed, view=self)


def event_info(
    name: str,
    points: int,
    date: str,
    code: str,
    resources: str,
    attendees: list[str] = [],
):
    embed = discord.Embed(title="Event Information", color=0xFFFFFF)
    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Points", value=points, inline=False)
    embed.add_field(name="Code", value=code, inline=False)
    embed.add_field(name="Date", value=date, inline=False)
    if resources:
        embed.add_field(name="Resources", value=resources, inline=False)
    if attendees:
        embed.add_field(name="Attendance count", value=len(attendees), inline=False)
    return embed


def event_list_embed(page: int):
    events = backend.event_list()
    max_pages = len(events) // 5 + 1
    names: str = ""
    dates: str = ""
    codes: str = ""
    selection = events[page * 5 : (page + 1) * 5]
    for event in selection:
        names += event["name"] + "\n"
        dates += event["date"] + "\n"
        codes += event["code"] + "\n"
    if len(names) == 0:
        return None

    embed = discord.Embed(
        title="Events",
        color=0xFFFFFF,
        description="find more info on an event by using /find_event name",
    )
    embed.add_field(name="Name", value=names, inline=True)
    embed.add_field(name="Date", value=dates, inline=True)
    embed.add_field(name="Code", value=codes, inline=True)

    embed.set_footer(text=f"page {page + 1}/{max_pages}")
    return embed


"""
Register Discord Bot Commands
"""


@reg.command(
    name="size", description="find the number of human members", guilds=guild_id
)
async def size(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "The GuildID is not set and the number of human members could not be verified."
        )
    else:
        count = 0
        for member in interaction.guild.members:
            if not member.bot:
                count += 1
        await interaction.response.send_message(
            f"There are {count} humans in the server."
        )


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="create",
    description="create an event and track its attendance",
    guilds=guild_id,
)
@app_commands.describe(
    name="The name of the event",
    points="The point value reward for attending",
    date="The date of the event",
    resources="Information to be shared with attendees",
)
async def create(
    interaction: discord.Interaction,
    name: str,
    points: int,
    date: str,
    resources: str = "",
):
    code = backend.create_event(name, points, date, resources, str(interaction.user.id))
    embed = event_info(name, points, date, code, resources)
    await interaction.response.send_message(f"The code is `{code}`", embed=embed)


class AttendModal(ui.Modal, title="Attend"):
    code = ui.TextInput(label="code")

    async def on_submit(self, interaction: discord.Interaction):
        code: str = self.code.value
        msg, event = backend.attend_event(code, str(interaction.user.id))
        if event is None:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        embed = event_info(
            event["name"], event["points"], event["date"], code, event["resources"]
        )
        await interaction.response.send_message(msg, embed=embed, ephemeral=True)


@app_commands.checks.cooldown(5, 30 * 60)
@reg.command(
    name="attend",
    description="register at the event you are attending for rewards and resources",
    guilds=guild_id,
)
@app_commands.describe(code="(optional) The code of the event given by the presenter")
async def attend(interaction: discord.Interaction, code: str = ""):
    if code == "":
        await interaction.response.send_modal(AttendModal())
        return
    msg, event = backend.attend_event(code, str(interaction.user.id))
    if event is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    embed = event_info(
        event["name"], event["points"], event["date"], code, event["resources"]
    )
    await interaction.response.send_message(msg, embed=embed, ephemeral=True)


@reg.command(
    name="leaderboard",
    description="find the top students with the highest points",
    guilds=guild_id,
)
@app_commands.describe(
    axis="what criteria to sort by", lim="the number of results to display"
)
async def leaderboard(
    interaction: discord.Interaction, axis: Literal["points", "attended"], lim: int = 10
):
    users = backend.leaderboard(axis, lim)
    if not users:
        await interaction.response.send_message("There are no registered users yet")
        return

    names_column = ""
    point_column = ""
    for user in users:
        names_column += user["name"] + "\n"
        point_column += f"{user["points"]}\n"
    embed = discord.Embed(title=f"{axis.capitalize()} Leaderboard", color=0xFFFFFF)
    embed.add_field(name="Name", value=names_column, inline=True)
    embed.add_field(name=f"{axis.capitalize()}", value=point_column, inline=True)
    await interaction.response.send_message(embed=embed)


@reg.command(
    name="leaderboard_search",
    description="find the top students with the highest points in all the events that include the search term",
    guilds=guild_id,
)
@app_commands.describe(activity="what activity group to search for")
async def leaderboard_search(interaction: discord.Interaction, activity: str):
    lb = backend.leaderboard_search(activity)
    if not lb:
        await interaction.response.send_message("There are no registered users yet")
        return
    prev, curr = 0, 0
    lb = sorted(lb, key=lambda kv: (kv[1], kv[0]), reverse=True)
    embeds: list[discord.Embed] = []
    while curr < len(lb):
        names_column = ""
        point_column = ""
        for name, point in lb[prev:]:
            if len(names_column) + len(name) + 1 > 1024:
                break
            names_column += name + "\n"
            point_column += f"{point}\n"
            curr += 1

        prev = curr
        embed = discord.Embed(title=f"Leaderboard for {activity}", color=0xFFFFFF)
        embed.add_field(name="Name", value=names_column, inline=True)
        embed.add_field(name=f"Attended", value=point_column, inline=True)
        embeds.append(embed)

    await interaction.response.send_message(embeds=embeds)
    # await interaction.response.send_message(f"The leaderboard for {activity}")


class RegisterModal(ui.Modal, title="Register"):
    name = ui.TextInput(
        label="name", placeholder="please enter your full name/names you go by"
    )
    grad_year = ui.TextInput(
        label="grad_year", placeholder="your graduation year (yyyy), e.g. 2024"
    )
    email = ui.TextInput(label="email", placeholder="TAMU email")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value
        grad_year = self.grad_year.value
        email = self.email.value
        try:
            msg: str = backend.register(
                name,
                grad_year,
                email,
                str(interaction.user.id),
                interaction.user.name,
                interaction.guild_id,
            )
        except:
            await client.get_channel(admin_channel_id).send(
                f"{interaction.user.mention} registration attempt, update token"
            )
            logger.debug(name, grad_year, email, interaction.user.name)
            msg = "The verification code failed to send, an officer has been notified and will contact you soon"
        await interaction.response.send_message(msg, ephemeral=True)


@reg.command(
    name="register", description="register your information here", guilds=guild_id
)
async def register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterModal())


@app_commands.checks.cooldown(3, 5 * 60)
@reg.command(name="verify", description="verify your TAMU email", guilds=guild_id)
@app_commands.describe(code="Please enter the code sent to your TAMU email")
async def verify(interaction: discord.Interaction, code: int):
    msg: str = backend.verify_email(code, str(interaction.user.id))
    if "verified!" in msg and interaction.guild_id == 631254092332662805:
        await interaction.user.add_roles(
            discord.Object(id=1015024081432743996), reason="TAMU email verified"
        )
    await interaction.response.send_message(msg, ephemeral=True)


@verify.error
async def on_verify_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CommandOnCooldown):
        backend.remove_pending(str(interaction.user.id))
        await interaction.response.send_message(
            "You have verified too many times! Please contact an officer",
            ephemeral=True,
        )


@reg.command(
    name="profile", description="get your current attendance info!", guilds=guild_id
)
async def profile(interaction: discord.Interaction):
    msg, user = backend.profile(str(interaction.user.id))
    if user is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    embed = discord.Embed(title="Profile", color=0xFFFFFF)
    embed.add_field(name="Name", value=user["name"], inline=False)
    embed.add_field(name="Points", value=user["points"], inline=False)
    embed.add_field(name="Attended Events", value=user["attended"], inline=False)
    if user["grad_year"] > 0:
        embed.add_field(name="Graduation Year", value=user["grad_year"], inline=False)
    if user["email"]:
        embed.add_field(name="TAMU Email", value=user["email"], inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@reg.command(
    name="profile_member",
    description="get the attendance info for a specific member!",
    guilds=guild_id,
)
@app_commands.default_permissions(manage_events=True)
@app_commands.describe(member="The profile for which member")
async def profile_member(interaction: discord.Interaction, member: discord.Member):
    msg, user = backend.profile(str(member.id))
    if user is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    embed = discord.Embed(title="Profile", color=0xFFFFFF)
    embed.add_field(name="Name", value=user["name"], inline=False)
    embed.add_field(name="Points", value=user["points"], inline=False)
    embed.add_field(name="Attended Events", value=user["attended"], inline=False)
    if user["grad_year"] > 0:
        embed.add_field(name="Graduation Year", value=user["grad_year"], inline=False)
    if user["email"]:
        embed.add_field(name="TAMU Email", value=user["email"], inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="find_event", description="get information on an event", guilds=guild_id
)
@app_commands.describe(code="Search by event code")
async def find_event(interaction: discord.Interaction, code: str = ""):
    msg, event = backend.find_event(code)
    if event is None:
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        embed = event_info(
            event["name"],
            event["points"],
            event["date"],
            code,
            event["resources"],
            event["attended_users"],
        )
        await interaction.response.send_message(embed=embed)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="event_list", description="get a list of all events created", guilds=guild_id
)
async def event_list(interaction: discord.Interaction):
    my_view = PageDisplay()
    embed = event_list_embed(0)
    if embed is None:
        await interaction.response.send_message("No events found", ephemeral=True)
        return
    await interaction.response.send_message(embed=embed, view=my_view)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="award", description="manually award points to a user", guilds=guild_id
)
@app_commands.describe(
    user="The user to award the points to", points="The number of points"
)
async def award(interaction: discord.Interaction, user: discord.Member, points: int):
    msg: str = backend.award(str(user.id), user.name, points)
    await interaction.response.send_message(msg)


# @app_commands.default_permissions(manage_events=True)
@reg.command(name="help", description="get a list of all commands", guilds=guild_id)
async def list_of_commands(interaction: discord.Interaction):
    commands = reg.get_commands()
    perm: bool = interaction.user.resolved_permissions.manage_events  # type: ignore
    output: str = ""

    if perm:
        for command in commands:
            if command.default_permissions is None:
                output += f"{command.name}\n"
            else:
                output += f"**{command.name}**\n"
    else:
        for command in commands:
            if command.default_permissions is None:
                output += f"{command.name}\n"

    await interaction.response.send_message(output)


class EditModal(discord.ui.Modal, title="Edit a Message"):
    answer = discord.ui.TextInput(
        label="Message content", style=discord.TextStyle.paragraph, max_length=2000
    )

    def __init__(self, message: discord.Message):
        super().__init__()
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        if self.message is None:
            await interaction.response.send_message(
                f"Howdy! The message has been sent.", ephemeral=True
            )
            await interaction.channel.send(f"{self.answer}")
        else:
            await interaction.response.send_message(
                f"Howdy! The message has been updated.", ephemeral=True
            )
            await self.message.edit(content=f"{self.answer}")


@app_commands.default_permissions(manage_events=True)
@reg.context_menu(name="Edit message", guilds=guild_id)
async def edit_message(
    interaction: discord.Interaction, message: discord.Message
) -> None:
    modal = EditModal(message)
    await interaction.response.send_modal(modal)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="send_editable_message",
    description="send a message that will be editable by user with permission configured in integrations",
    guilds=guild_id,
)
async def send_editable_message(interaction: discord.Interaction) -> None:
    modal = EditModal()
    await interaction.response.send_modal(modal)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="update_calendar_events",
    description="create discord events for google calendar events",
    guilds=guild_id,
)
async def update_calendar_events(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "No GuildID found in discord interaction."
        )
        return

    events = backend.calendar_events()
    discord_events = [
        {"name": event.name, "start": event.start_time, "end": event.end_time}
        for event in interaction.guild.scheduled_events
    ]

    if events is None:
        await interaction.response.send_message("No events found", ephemeral=True)
        return

    msg = f"Imported {len(events)} events from calendar."
    await interaction.response.send_message(msg)
    count = 0
    newmsg: str = ""
    for event in events:
        event_data = {
            "name": event["name"],
            "start": event["start"],
            "end": event["end"],
        }
        if event_data not in discord_events:
            try:
                await interaction.guild.create_scheduled_event(
                    name=event["name"],
                    start_time=event["start"],
                    end_time=event["end"],
                    privacy_level=PrivacyLevel.guild_only,
                    entity_type=EntityType.external,
                    location=event["location"],
                )
                count += 1
            except discord.Forbidden:
                await interaction.followup.send(
                    "I don't have permission to create events in this server."
                )
                return
            except discord.HTTPException:
                newmsg += "There was an error creating an event. Has the event already started?\n"

    if count != 0:
        newmsg += f"Added {count} server events to the server."
    else:
        newmsg += "All calendar events already in the discord."
    await interaction.followup.send(newmsg)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="delete_all_events",
    description="delete all current discord events",
    guilds=guild_id,
)
async def delete_all_events(interaction: discord.Interaction):
    num_events = len(interaction.guild.scheduled_events)
    msg = f"Deleting {num_events} events from server."
    await interaction.response.send_message(msg)
    for event in interaction.guild.scheduled_events:
        await event.delete()


activity_group_channels = {
    "cyber op": 1278359289160929332,
    "hardware": 1146555338464694424,
    "aws": 1280195306733961236,
    "palo": 986388231052460092,
    "cisco": 946612171360579627,
}


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="generate_announcements",
    description="generates announcements boilerplate based on events",
    guilds=guild_id,
)
async def generate_announcements(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    # Current datetime
    dt_now = dt.now()

    # Weekday
    weekday_now = dt_now.weekday()

    # First day of the week (Monday) (https://stackoverflow.com/questions/39441639/getting-the-date-of-the-first-day-of-the-week/61743379#61743379)
    monday = (dt.today() - timedelta(days=dt.today().weekday() % 7)).date()
    friday = monday + timedelta(days=4)

    # Create dictionary of events to sort
    events = dict(
        [(key, {}) for key in [x for x in range(5)]]
    )  # cursed list comprehension
    events_announced = 0

    boilerplate = """
        # Howdy everyone! <:sunglasses_cowboy:916376081576116354>
        Here's what we have for this week
    """

    for event in await interaction.guild.fetch_scheduled_events():
        start_time = event.start_time.astimezone(timezone("US/Central"))
        end_time = event.end_time.astimezone(timezone("US/Central"))

        if 0 <= weekday_now <= 4:
            if monday <= start_time.date() <= friday:
                events_announced += 1

                if not event.location in events[start_time.weekday()]:
                    events[start_time.weekday()][event.location] = [event]
                else:
                    events[start_time.weekday()][event.location].append(event)

    for weekday, locations in events.items():
        if len(locations) > 0:
            boilerplate += f"\n## __{day_name[weekday]}__:\n"

            for location, events in locations.items():
                if len(events) > 0:
                    bldg = location.split(" ")[0]

                    # hacky method - concatenate location to url to get the map
                    if len(bldg) == 3 or len(bldg) == 4:
                        boilerplate += f"**{location}** ([Map](<https://aggiemap.tamu.edu/map/d?bldg={location.split(' ')[0]}>))\n"
                    else:
                        boilerplate += f"**{location}**\n"

                    for event in events:
                        start_time = (
                            event.start_time.astimezone(timezone("US/Central"))
                            .strftime("%I:%M%p")
                            .lstrip("0")
                            .replace(" 0", " ")
                        )
                        end_time = (
                            event.end_time.astimezone(timezone("US/Central"))
                            .strftime("%I:%M%p")
                            .lstrip("0")
                            .replace(" 0", " ")
                        )

                        channel_mention = ""
                        for key, value in activity_group_channels.items():
                            print(key, value, event.name)
                            if key in event.name.lower():
                                channel_mention = f"<#{value}> "
                                break
                        print(channel_mention)
                        boilerplate += f"- **[{event.name}](<{event.url}>)** | {channel_mention}{start_time} - {end_time}\n"

    if events_announced == 0:
        await interaction.followup.send("No events for this week.")
    else:
        await interaction.followup.send(boilerplate)


client.run(discord_token)
