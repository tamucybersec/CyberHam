import logging
from typing import cast
from pytz import timezone

import discord
from discord import app_commands
from discord import ScheduledEvent
from discord.ext import ipcx

import cyberham.backend.events as backend_events
from cyberham import guild_id, discord_token, admin_channel_id
from cyberham.bot.utils import event_info
from cyberham.types import Category
from cyberham import ipc_key, ipc_port


class Bot(discord.Client):
    logger: logging.Logger
    command_tree: app_commands.CommandTree

    def __init__(self):
        super().__init__(
            intents=discord.Intents(
                guilds=True, members=True, messages=True, reactions=True, guild_scheduled_events=True
            )
        )
        self.synced = False
        self.logger = logging.getLogger(__name__)
        self.command_tree = app_commands.CommandTree(self)
        self.ipc = ipcx.Server(self, secret_key=ipc_key, port=ipc_port)
    
    async def setup_hook(self) -> None:
        await self.ipc.start()

    async def on_ipc_ready(self) -> None:
        print("IPC server starting")
    
    async def on_ipc_error(self, endpoint, error) -> None:
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
    from cyberham.bot import admin
    from cyberham.bot import announcements
    from cyberham.bot import events
    from cyberham.bot import leaderboard
    from cyberham.bot import users
    from cyberham.bot import rsvp

    bot = Bot()

    @bot.ipc.route()
    async def test(data: object) -> str:
        try:
            user = bot.get_user(data.user_id)
            if user is None:
                user = await bot.fetch_user(data.user_id)
        except Exception as e:
            print("found exception:",e)
        return str(user)
    
    admin.setup_commands(bot)
    announcements.setup_commands(bot)
    rsvp.setup_commands(bot)
    events.setup_commands(bot)
    leaderboard.setup_commands(bot)
    users.setup_commands(bot)
    bot.run(discord_token)
