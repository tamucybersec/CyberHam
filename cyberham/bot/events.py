from typing import Any

import discord
from discord import app_commands
import cyberham.backend.events as backend_events
from cyberham import guild_id
from cyberham.bot.bot import Bot
from cyberham.bot.ui import AttendModal, PageDisplay
from cyberham.bot.utils import event_info, event_list_embed, handle_attend_response


def setup_commands(bot: Bot):
    command_tree = bot.command_tree

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="create",
        description="create an event and track its attendance",
        guilds=guild_id,
    )
    @app_commands.describe(
        name="The name of the event",
        points="The point value reward for attending",
        date="The date of the event",
    )
    async def create(
        interaction: discord.Interaction,
        name: str,
        points: int,
        date: str,
    ):
        code = backend_events.create_event(name, points, date)
        embed = event_info(name, points, date, code, 0)
        await interaction.response.send_message(f"The code is `{code}`", embed=embed)

    @app_commands.checks.cooldown(5, 30 * 60)
    @command_tree.command(
        name="attend",
        description="register at the event you are attending for rewards",
        guilds=guild_id,
    )
    @app_commands.describe(
        code="(optional) The code of the event given by the presenter"
    )
    async def attend(interaction: discord.Interaction, code: str = ""):
        if code == "":
            await interaction.response.send_modal(AttendModal())
            return
        await handle_attend_response(interaction, code)

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="find_event", description="get information on an event", guilds=guild_id
    )
    @app_commands.describe(code="Search by event code")
    async def find_event(interaction: discord.Interaction, code: str = ""):
        msg, event, attendance = backend_events.find_event(code)
        if event is None:
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            embed = event_info(
                event["name"],
                event["points"],
                event["date"],
                code,
                attendance,
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="event_list",
        description="get a list of all events created",
        guilds=guild_id,
    )
    async def event_list(interaction: discord.Interaction):
        page_view = PageDisplay()
        embed = event_list_embed(0)
        if embed is None:
            await interaction.response.send_message("No events found", ephemeral=True)
            return
        await interaction.response.send_message(embed=embed, view=page_view)

    # satisfy type checker
    _: list[Any] = [create, attend, find_event, event_list]
