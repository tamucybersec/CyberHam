import random
import string

# pip3 install git+https://github.com/Rapptz/discord.py
import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import sqlite3
from typing import Literal
from dataclasses import dataclass
from datetime import datetime

from cyberclub_email import CyberClub

conn = sqlite3.connect('attendance.db')
c = conn.cursor()
# users: user_id, name, points, attended_dates, grad_year, tamu_email
c.execute(
    "CREATE TABLE IF NOT EXISTS "
    "users(user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER, attended INTEGER, grad_year INTEGER, email TEXT)")
# events: name, code, points, date (mm/dd/yy), resources, attended_users
c.execute(
    "CREATE TABLE IF NOT EXISTS "
    "events(name TEXT, code TEXT PRIMARY KEY, points INTEGER, date TEXT, resources TEXT, attended_users TEXT)")
conn.commit()

pending_emails = {}

guild_id = 805821298193465384

out_mail = CyberClub()


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents(guilds=True, members=True, messages=True, reactions=True))
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await reg.sync(guild=discord.Object(id=guild_id))
            self.synced = True
        print('bot online')


@dataclass
class EmailPending:
    user_id: int
    email: str
    code: int
    time: datetime


load_dotenv()
client = Bot()
reg = app_commands.CommandTree(client)


@reg.command(name="size", description="find the number of human members", guild=discord.Object(id=guild_id))
async def size(interaction: discord.Interaction):
    count = 0
    for member in interaction.guild.members:
        if not member.bot:
            count += 1
    await interaction.response.send_message(f"There are {count} humans in the server.")


def event_info(name, points, date, resources):
    embed = discord.Embed(title="Event Information", color=0xFFFFFF)
    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Points", value=points, inline=False)
    embed.add_field(name="Date", value=date, inline=False)
    if resources:
        embed.add_field(name="Resources", value=resources, inline=False)
    return embed


@app_commands.default_permissions(manage_events=True)
@reg.command(name="create", description="create an event and track its attendance",
             guild=discord.Object(id=guild_id))
async def create(interaction: discord.Interaction, name: str, points: int, date: str, resources: str = ""):
    code = ''
    code_list = [0]
    while code_list is not None:
        code = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
        c.execute("SELECT name FROM events WHERE code = ?", (code,))
        code_list = c.fetchone()  # returns tuple of one if exists otherwise none

    c.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, '')", (name, code, points, date, resources))
    conn.commit()
    embed = event_info(name, points, date, resources)
    await interaction.response.send_message(f"The code is `{code}`", embed=embed)


@reg.command(name="attend", description="register at the event you are attending for rewards and resources",
             guild=discord.Object(id=guild_id))
async def attend(interaction: discord.Interaction, code: str):
    code = code.upper()
    # print(f"{interaction.user.name} has attended {code}")
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, 0, 0, 0, '')", (interaction.user.id, interaction.user.name))
    conn.commit()
    c.execute("SELECT * FROM events WHERE code = ?", (code,))
    temp = c.fetchone()
    if temp is None:
        await interaction.response.send_message(f'{code} does not exist!', ephemeral=True)
        return
    name, _, points, date, resources, attended_users = temp
    if str(interaction.user.id) in attended_users.split():
        await interaction.response.send_message(f'You have already redeemed {code}!', ephemeral=True)
        return

    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, interaction.user.id))
    c.execute("UPDATE users SET attended = attended + 1 WHERE user_id = ?", (interaction.user.id,))
    c.execute("UPDATE events SET attended_users = attended_users || ?", (f" {interaction.user.id}",))
    conn.commit()
    embed = event_info(name, points, date, resources)
    await interaction.response.send_message(f'Successfully registered for {code}!', embed=embed, ephemeral=True)


@reg.command(name="leaderboard", description="find the top students with the highest points",
             guild=discord.Object(id=guild_id))
async def leaderboard(interaction: discord.Interaction, axis: Literal['points', 'attended'], lim: int = 10):
    if axis == 'points':
        c.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT ?", (lim,))
    else:
        c.execute("SELECT name, attended FROM users ORDER BY attended DESC LIMIT ?", (lim,))
    lb = c.fetchall()
    if not lb:
        await interaction.response.send_message("There are no registered users yet")
        return

    names_column = ''
    point_column = ''
    for name, point in lb:
        names_column += name + '\n'
        point_column += f'{point}\n'
    embed = discord.Embed(title=f"{axis.capitalize()} Leaderboard", color=0xFFFFFF)
    embed.add_field(name="Name", value=names_column, inline=True)
    embed.add_field(name=f"{axis.capitalize()}", value=point_column, inline=True)
    await interaction.response.send_message(embed=embed)


@reg.command(name="register", description="register your information here",
             guild=discord.Object(id=guild_id))
async def register(interaction: discord.Interaction, name: str, grad_year: int, email: str):
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, 0, 0, 0, '')", (interaction.user.id, interaction.user.name))
    conn.commit()
    if not 1950 < grad_year < 2030:
        await interaction.response.send_message("Please set your graduation year in the format of 202X",
                                                ephemeral=True)
        return

    email = email.lower()
    if not ('@' in email and email.endswith('tamu.edu')):
        await interaction.response.send_message("Please set a proper TAMU email address", ephemeral=True)
        return
    c.execute("SELECT email FROM users WHERE user_id = ?", (interaction.user.id,))
    temp = c.fetchone()
    if temp is not None and temp[0] == email:
        ask_to_verify = ""
    else:
        verification = EmailPending(interaction.user.id, email, random.randint(1000, 10000), datetime.now())
        pending_emails[interaction.user.id] = verification
        out_mail.send_email(email, str(verification.code))
        ask_to_verify = "Please use /verify with the code you received in your email"

    c.execute("UPDATE users SET name = ?, grad_year = ? WHERE user_id = ?",
              (name, grad_year, interaction.user.id))
    conn.commit()
    await interaction.response.send_message(f"You have successfully updated your profile! {ask_to_verify}",
                                            ephemeral=True)


@reg.command(name="verify", description="verify your TAMU email", guild=discord.Object(id=guild_id))
async def verify(interaction: discord.Interaction, code: int):
    if interaction.user.id in pending_emails:
        pend_email = pending_emails[interaction.user.id]
        if pend_email.code == code:
            c.execute("UPDATE users SET email = ? WHERE user_id = ?", (pend_email.email, interaction.user.id))
            conn.commit()
            await interaction.response.send_message("Email verified! It is now visible on your /profile")
            pending_emails.pop(interaction.user.id)
            return
        else:
            await interaction.response.send_message("This code is not correct!", ephemeral=True)
            return
    else:
        await interaction.response.send_message("Please use /register to submit your email", ephemeral=True)


@reg.command(name="profile", description="get your current attendance info!",
             guild=discord.Object(id=guild_id))
async def profile(interaction: discord.Interaction):
    c.execute('SELECT name, points, attended, grad_year, email FROM users WHERE user_id = ?', (interaction.user.id,))
    _temp = c.fetchone()
    if _temp is None:
        await interaction.response.send_message("This profile does not exist", ephemeral=True)
        return
    name, points, attended, grad_year, email = _temp
    embed = discord.Embed(title="Profile", color=0xFFFFFF)
    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Points", value=points, inline=False)
    embed.add_field(name="Attended Events", value=attended, inline=False)
    if grad_year > 0:
        embed.add_field(name="Graduation Year", value=grad_year, inline=False)
    if email:
        embed.add_field(name="TAMU Email", value=email, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@app_commands.default_permissions(manage_events=True)
@reg.command(name="find_event", description="get information on an event",
             guild=discord.Object(id=guild_id))
async def find_event(interaction: discord.Interaction, code: str = "", name: str = ""):
    if name == "" and code == "":
        await interaction.response.send_message("Please include an event name or code.", ephemeral=True)
        return
    elif code == "":
        c.execute("SELECT name, points, date, resources FROM events WHERE name = ?", (name,))
    elif name == "":
        c.execute("SELECT name, points, date, resources FROM events WHERE code = ?", (code,))
    else:
        c.execute("SELECT name, points, date, resources FROM events where name = ? AND code = ?", (name, code))

    temp = c.fetchone()
    if temp is None:
        await interaction.response.send_message("This event does not exist", ephemeral=True)
    else:
        name, points, date, resources = temp
        embed = event_info(name, points, date, resources)
        await interaction.response.send_message(embed=embed, ephemeral=True)


@reg.command(name="event_list", description="get a list of all events created", guild=discord.Object(id=guild_id))
async def event_list(interaction: discord.Interaction):
    c.execute("SELECT name, date FROM events")
    events = c.fetchall()[::-1]
    names = ''
    dates = ''
    selection = events[0:5]
    for event in selection:
        names += event[0] + '\n'
        dates += event[1] + '\n'
    if len(names) == 0:
        await interaction.response.send_message("there are no events created yet", ephemeral=True)
        return
    embed = discord.Embed(title="Events", color=0xFFFFFF)
    embed.add_field(name="Name", value=names, inline=True)
    embed.add_field(name="Date", value=dates, inline=True)
    embed.set_footer(text='page 1')
    await interaction.response.send_message(embed=embed)


@app_commands.default_permissions(manage_events=True)
@reg.command(name="award", description="manually award points to a user", guild=discord.Object(id=guild_id))
async def award(interaction: discord.Interaction, user: discord.Member, points: int):
    c.execute("SELECT name FROM users WHERE user_id = ?", (user.id,))
    name = c.fetchone()
    if name is None:
        await interaction.response.send_message("This user has not registered yet!")
    else:
        name = name[0]
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user.id))
    conn.commit()
    await interaction.response.send_message(f"Successfully added {points} points to {user.name} - {name}")

client.run(os.environ['DISCORD_TOKEN'])
