import os
from typing import Literal

import discord
from discord import app_commands

import cyberham.backend as backend
from cyberham.config import guild_id, discord_token

"""
Define Bot Attributes
"""


class Bot(discord.Client):
    def __init__(self):
        super().__init__(
            intents=discord.Intents(
                guilds=True, members=True, messages=True, reactions=True
            )
        )
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await reg.sync(guild=discord.Object(id=guild_id))
            self.synced = True
        print("bot online")


client = Bot()
reg = app_commands.CommandTree(client)

"""
Discord Bot UI
"""


class PageDisplay(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.response = (
            None  # Define a variable named response with the initial value set to None
        )

    @discord.ui.button(
        style=discord.ButtonStyle.primary, custom_id="el_next", label="1", emoji="▶"
    )
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        page = int(button.label)
        button.label = page + 1
        embed = event_list_embed(page)
        await interaction.response.edit_message(embed=embed, view=self)


def event_info(name, points, date, resources):
    embed = discord.Embed(title="Event Information", color=0xFFFFFF)
    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Points", value=points, inline=False)
    embed.add_field(name="Date", value=date, inline=False)
    if resources:
        embed.add_field(name="Resources", value=resources, inline=False)
    return embed


def event_list_embed(page):
    events = backend.event_list()
    max_pages = len(events) // 5 + 1
    names = ""
    dates = ""
    selection = events[page * 5 : (page + 1) * 5]
    for event in selection:
        names += event[0] + "\n"
        dates += event[1] + "\n"
    if len(names) == 0:
        return None

    embed = discord.Embed(
        title="Events",
        color=0xFFFFFF,
        description="find more info on an event by using /find_event name",
    )
    embed.add_field(name="Name", value=names, inline=True)
    embed.add_field(name="Date", value=dates, inline=True)

    embed.set_footer(text=f"page {page + 1}/{max_pages}")
    return embed


"""
Register Discord Bot Commands
"""


@reg.command(
    name="size",
    description="find the number of human members",
    guild=discord.Object(id=guild_id),
)
async def size(interaction: discord.Interaction):
    count = 0
    for member in interaction.guild.members:
        if not member.bot:
            count += 1
    await interaction.response.send_message(f"There are {count} humans in the server.")


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="create",
    description="create an event and track its attendance",
    guild=discord.Object(id=guild_id),
)
async def create(
    interaction: discord.Interaction,
    name: str,
    points: int,
    date: str,
    resources: str = "",
):
    code = backend.create_event(name, points, date, resources)
    embed = event_info(name, points, date, resources)
    await interaction.response.send_message(f"The code is `{code}`", embed=embed)


@reg.command(
    name="attend",
    description="register at the event you are attending for rewards and resources",
    guild=discord.Object(id=guild_id),
)
async def attend(interaction: discord.Interaction, code: str):
    msg, data = backend.attend_event(code, interaction.user.id, interaction.user.name)
    if data is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    name, points, date, resources = data
    embed = event_info(name, points, date, resources)
    await interaction.response.send_message(msg, embed=embed, ephemeral=True)


@reg.command(
    name="leaderboard",
    description="find the top students with the highest points",
    guild=discord.Object(id=guild_id),
)
async def leaderboard(
    interaction: discord.Interaction, axis: Literal["points", "attended"], lim: int = 10
):
    lb = backend.leaderboard(axis, lim)
    if not lb:
        await interaction.response.send_message("There are no registered users yet")
        return

    names_column = ""
    point_column = ""
    for name, point in lb:
        names_column += name + "\n"
        point_column += f"{point}\n"
    embed = discord.Embed(title=f"{axis.capitalize()} Leaderboard", color=0xFFFFFF)
    embed.add_field(name="Name", value=names_column, inline=True)
    embed.add_field(name=f"{axis.capitalize()}", value=point_column, inline=True)
    await interaction.response.send_message(embed=embed)


@reg.command(
    name="register",
    description="register your information here",
    guild=discord.Object(id=guild_id),
)
async def register(
    interaction: discord.Interaction, name: str, grad_year: int, email: str
):
    msg = backend.register(
        name, grad_year, email, interaction.user.id, interaction.user.name
    )
    await interaction.response.send_message(msg, ephemeral=True)


@reg.command(
    name="verify",
    description="verify your TAMU email",
    guild=discord.Object(id=guild_id),
)
async def verify(interaction: discord.Interaction, code: int):
    msg = backend.verify_email(code, interaction.user.id)
    await interaction.response.send_message(msg, ephemeral=True)


@reg.command(
    name="profile",
    description="get your current attendance info!",
    guild=discord.Object(id=guild_id),
)
async def profile(interaction: discord.Interaction):
    msg, data = backend.profile(interaction.user.id)
    if data is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    name, points, attended, grad_year, email = data
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
@reg.command(
    name="find_event",
    description="get information on an event",
    guild=discord.Object(id=guild_id),
)
async def find_event(interaction: discord.Interaction, code: str = "", name: str = ""):
    msg, data = backend.find_event(code, name)
    if data is None:
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        name, points, date, resources = data
        embed = event_info(name, points, date, resources)
        await interaction.response.send_message(embed=embed)


@reg.command(
    name="event_list",
    description="get a list of all events created",
    guild=discord.Object(id=guild_id),
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
    name="award",
    description="manually award points to a user",
    guild=discord.Object(id=guild_id),
)
async def award(interaction: discord.Interaction, user: discord.Member, points: int):
    msg = backend.award(user.id, user.name, points)
    await interaction.response.send_message(msg)


client.run(discord_token)
