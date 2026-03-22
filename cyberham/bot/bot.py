import logging
from typing import cast
from pytz import timezone

import discord
from discord import app_commands
from discord import ScheduledEvent

import cyberham.backend.events as backend_events
from cyberham import guild_id, discord_token, admin_channel_id
from cyberham.bot.utils import event_info
from cyberham.types import Category


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

    async def on_ready(self):
        await self.wait_until_ready()
        for g in guild_id:
            await self.command_tree.sync(guild=g)
            print("synced server", g.id)
        self.synced = True
        print("bot online")
        self.loop.create_task(self.update_usernames())

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

    async def update_usernames(self):
        import sqlite3
        async def f(user_id: int) -> str:
            user = self.get_user(user_id)
            if user: return user.name
            try:
                user = await self.fetch_user(user_id)
                return user.name
            except discord.NotFound:
                return "user not found"
            except discord.HTTPException:
                return "error fetching user"
        
        try: 
            with sqlite3.connect("cyberham.db") as conn:
                cursor = conn.cursor()
                cursor.execute("select user_id from users")
                rows = cursor.fetchall()
                for row in rows:
                    username = await f(int(row[0]))
                    cursor.execute('''update users set username = ? where user_id = ?''', (username, row[0]))
                    conn.commit()
                cursor.close()
        except Exception as e:
            print("Error updating usernames:", e)
            return
        print("Usernames updated successfully")

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
    admin.setup_commands(bot)
    announcements.setup_commands(bot)
    rsvp.setup_commands(bot)
    events.setup_commands(bot)
    leaderboard.setup_commands(bot)
    users.setup_commands(bot)
    bot.run(discord_token)
