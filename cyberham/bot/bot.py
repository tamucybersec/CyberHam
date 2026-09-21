import logging
from typing import cast

import discord
from discord import ScheduledEvent, app_commands
from discord.ext import commands, ipcx
from pytz import timezone

import cyberham.backend.events as backend_events
from cyberham import admin_channel_id, discord_token, guild_id, ipc_key, ipc_port
from cyberham.bot.ui import RSVPButton
from cyberham.bot.utils import event_info
from cyberham.types import Category


class FetchUserPayload:
    user_id: int


class Bot(discord.Client):
    logger: logging.Logger
    command_tree: app_commands.CommandTree

    def __init__(self):
        super().__init__(
            intents=discord.Intents(
                guilds=True,
                members=True,
                messages=True,
                reactions=True,
                guild_scheduled_events=True,
            )
        )
        self.synced = False
        self.logger = logging.getLogger(__name__)
        self.command_tree = app_commands.CommandTree(self)
        self.ipc = ipcx.Server(
            cast(commands.Bot, self), port=ipc_port, secret_key=ipc_key
        )

    async def setup_hook(self) -> None:
        self.add_dynamic_items(RSVPButton)
        await self.ipc.start()

    async def on_ipc_ready(self) -> None:
        print("IPC server starting")

    async def on_ipc_error(self, endpoint: str, error: Exception) -> None:
        print(endpoint, "raised", error)

    async def on_ready(self):
        await self.wait_until_ready()
        for g in guild_id:
            await self.command_tree.sync(guild=g)
            print("synced server", g.id)
        self.synced = True
        print("bot online")

    async def on_scheduled_event_create(self, event: ScheduledEvent):
        # voice channel events do not trigger this
        points = 50
        time = event.start_time.astimezone(timezone("US/Central"))
        category = event.description or ""

        code, err = backend_events.create_event(
            event.name, points, time.strftime("%m/%d/%Y"), cast(Category, category)
        )
        channel = cast(discord.TextChannel, self.get_channel(admin_channel_id))
        if err is not None:
            await channel.send(err.message)
        else:
            embed = event_info(event.name, points, time.strftime("%m/%d/%Y"), code, 0)
            await channel.send(f"The code is `{code}`", embed=embed)


def run_bot():
    # hand off the command tree so the commands can register themselves
    # imported inside the function to prevent a circular import
    from cyberham.bot import admin, announcements, events, leaderboard, rsvp, users

    bot = Bot()

    @bot.ipc.route()  # type: ignore
    async def fetch_username(data: FetchUserPayload) -> str:
        user = bot.get_user(data.user_id)
        if user is None:
            user = await bot.fetch_user(data.user_id)
        return str(user)

    admin.setup_commands(bot)
    announcements.setup_commands(bot)
    rsvp.setup_commands(bot)
    events.setup_commands(bot)
    leaderboard.setup_commands(bot)
    users.setup_commands(bot)
    bot.run(discord_token)
