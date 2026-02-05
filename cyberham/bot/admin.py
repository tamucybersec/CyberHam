from typing import Any

import discord
from discord import app_commands
from discord import EntityType
from discord import PrivacyLevel
from datetime import datetime as dt

import cyberham.backend.events as backend_events
import cyberham.backend.users as backend_users
from cyberham import guild_id
from cyberham.bot.bot import Bot
from cyberham.bot.ui import EditModal
from cyberham.bot.utils import valid_guild
from cyberham.utils.logger import log_elevated_operation


def setup_commands(bot: Bot):
    command_tree = bot.command_tree

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="award", description="manually award points to a user", guilds=guild_id
    )
    @app_commands.describe(
        user="The user to award the points to", points="The number of points"
    )
    async def award(
        interaction: discord.Interaction, user: discord.Member, points: int
    ):
        log_elevated_operation(
            operation="award_points",
            user_id=str(interaction.user.id),
            user_name=interaction.user.name,
            details=f"Awarded {points} points to {user.name} (ID: {user.id})"
        )
        msg: str = backend_users.award(str(user.id), user.name, points)
        await interaction.response.send_message(msg)

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="delete_all_events",
        description="delete all current discord events",
        guilds=guild_id,
    )
    async def delete_all_events(interaction: discord.Interaction):
        if not await valid_guild(interaction):
            return
        assert interaction.guild is not None

        num_events = len(interaction.guild.scheduled_events)
        
        log_elevated_operation(
            operation="delete_all_events",
            user_id=str(interaction.user.id),
            user_name=interaction.user.name,
            details=f"Deleting {num_events} Discord events"
        )
        
        msg = f"Deleting {num_events} events from server."
        await interaction.response.send_message(msg)
        for event in interaction.guild.scheduled_events:
            await event.delete()

    @app_commands.default_permissions(manage_events=True)
    @command_tree.context_menu(name="Edit message", guilds=guild_id)
    async def edit_message(
        interaction: discord.Interaction, message: discord.Message
    ) -> None:
        modal = EditModal(message)
        await interaction.response.send_modal(modal)

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="send_editable_message",
        description="send a message that will be editable by user with permission configured in integrations",
        guilds=guild_id,
    )
    async def send_editable_message(interaction: discord.Interaction) -> None:
        modal = EditModal()
        await interaction.response.send_modal(modal)

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="update_calendar_events",
        description="create discord events for google calendar events",
        guilds=guild_id,
    )
    async def update_calendar_events(interaction: discord.Interaction):
        if not await valid_guild(interaction):
            return
        assert interaction.guild is not None

        log_elevated_operation(
            operation="update_calendar_events",
            user_id=str(interaction.user.id),
            user_name=interaction.user.name,
            details="Importing events from Google Calendar to Discord"
        )

        events, err = backend_events.calendar_events()
        if err is not None:
            await interaction.response.send_message(err.message, ephemeral=True)
            return
        if not events:
            await interaction.response.send_message("No events found", ephemeral=True)
            return

        discord_events: list[dict[str, str | dt | None]] = [
            {"name": event.name, "start": event.start_time, "end": event.end_time}
            for event in interaction.guild.scheduled_events
        ]

        msg = f"Imported {len(events)} events from calendar. Creating discord scheduled events..."
        await interaction.response.send_message(msg)

        count = 0
        new_msg: str = ""
        for event in events:
            event_data: dict[str, str | dt | None] = {
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
                        description=event["category"]
                    )
                    count += 1

                except discord.Forbidden:
                    await interaction.followup.send(
                        "I don't have permission to create events in this server."
                    )
                    return
                except discord.HTTPException:
                    new_msg += "There was an error creating an event. Has the event already started?\n"

        if count != 0:
            new_msg += f"Added {count} server events to the server."
        else:
            new_msg += "All calendar events already in the discord."

        await interaction.followup.send(new_msg)

    # satisfy type checker
    _: list[Any] = [
        award,
        delete_all_events,
        edit_message,
        send_editable_message,
        update_calendar_events,
    ]
