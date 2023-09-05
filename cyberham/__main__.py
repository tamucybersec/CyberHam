from typing import Literal

import discord
from discord import app_commands

import cyberham.backend as backend
from cyberham import guild_id, discord_token

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
        for g in guild_id:
            await reg.sync(guild=g)
        self.synced = True
        print("bot online")


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

    @discord.ui.button(
        style=discord.ButtonStyle.primary, custom_id="el_next", label="1", emoji="▶"
    )
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        page = int(button.label)
        button.label = page + 1
        embed = event_list_embed(page)
        if embed is None:
            await interaction.response.defer()
            return
        await interaction.response.edit_message(embed=embed, view=self)


def event_info(name, points, date, code, resources, attendees=""):
    embed = discord.Embed(title="Event Information", color=0xFFFFFF)
    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Points", value=points, inline=False)
    embed.add_field(name="Code", value=code, inline=False)
    embed.add_field(name="Date", value=date, inline=False)
    if resources:
        embed.add_field(name="Resources", value=resources, inline=False)
    if attendees != "":
        count = len(attendees.split(" "))
        embed.add_field(name="Attendance count", value=count, inline=False)
    return embed


def event_list_embed(page):
    events = backend.event_list()
    max_pages = len(events) // 5 + 1
    names = ""
    dates = ""
    codes = ""
    selection = events[page * 5: (page + 1) * 5]
    for event in selection:
        names += event[0] + "\n"
        dates += event[1] + "\n"
        codes += event[2] + "\n"
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
    name="size",
    description="find the number of human members",
    guilds=guild_id
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
    guilds=guild_id
)
@app_commands.describe(
    name='The name of the event',
    points='The point value reward for attending',
    date='The date of the event',
    resources='Information to be shared with attendees'
)
async def create(
        interaction: discord.Interaction,
        name: str,
        points: int,
        date: str,
        resources: str = "",
):
    code = backend.create_event(name, points, date, resources, interaction.user.id)
    embed = event_info(name, points, date, code, resources)
    await interaction.response.send_message(f"The code is `{code}`", embed=embed)


@app_commands.checks.cooldown(5, 30 * 60)
@reg.command(
    name="attend",
    description="register at the event you are attending for rewards and resources",
    guilds=guild_id
)
@app_commands.describe(code='The code of the event given by the presenter')
async def attend(interaction: discord.Interaction, code: str):
    msg, data = backend.attend_event(code, interaction.user.id, interaction.user.name)
    if data is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    name, points, date, resources = data
    embed = event_info(name, points, date, code, resources)
    await interaction.response.send_message(msg, embed=embed, ephemeral=True)


@reg.command(
    name="leaderboard",
    description="find the top students with the highest points",
    guilds=guild_id
)
@app_commands.describe(
    axis='what criteria to sort by',
    lim='the number of results to display'
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
    guilds=guild_id
)
@app_commands.describe(
    name='please enter your full name/names you go by',
    grad_year='your graduation year (yyyy)',
    email='TAMU email'
)
async def register(
        interaction: discord.Interaction, name: str, grad_year: int, email: str
):
    try:
        msg = backend.register(
            name, grad_year, email, interaction.user.id, interaction.user.name, interaction.guild_id
        )
    except:
        await client.get_channel(1014740464601153536) \
            .send(f"{interaction.user.mention} registration attempt, update token")
        print(name, grad_year, email, interaction.user.name)
        msg = "The verification code failed to send, an officer has been notified and will contact you soon"
    await interaction.response.send_message(msg, ephemeral=True)


@app_commands.checks.cooldown(3, 5 * 60)
@reg.command(
    name="verify",
    description="verify your TAMU email",
    guilds=guild_id
)
@app_commands.describe(code='Please enter the code sent to your TAMU email')
async def verify(interaction: discord.Interaction, code: int):
    msg = backend.verify_email(code, interaction.user.id)
    if 'verified!' in msg and interaction.guild_id == 631254092332662805:
        await interaction.user.add_roles(discord.Object(id=1015024081432743996), reason='TAMU email verified')
    await interaction.response.send_message(msg, ephemeral=True)


@verify.error
async def on_verify_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        backend.remove_pending(interaction.user.id)
        await interaction.response.send_message("You have verified too many times! Please contact an officer",
                                                ephemeral=True)


@reg.command(
    name="profile",
    description="get your current attendance info!",
    guilds=guild_id
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

@reg.command(
    name="profile_member",
    description="get the attendance info for a specific member!",
    guilds=guild_id
)
@app_commands.default_permissions(manage_events=True)
@app_commands.describe(member="The profile for which member")
async def profile(interaction: discord.Interaction, member: discord.Member):
    msg, data = backend.profile(member.id)
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
    guilds=guild_id
)
@app_commands.describe(
    code='Search by event code',
    name='Search by the exact event name'
)
async def find_event(interaction: discord.Interaction, code: str = "", name: str = ""):
    msg, data = backend.find_event(code, name)
    if data is None:
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        name, points, date, code, resources, attendees = data
        embed = event_info(name, points, date, code, resources, attendees)
        await interaction.response.send_message(embed=embed)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="event_list",
    description="get a list of all events created",
    guilds=guild_id
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
    guilds=guild_id
)
@app_commands.describe(
    user='The user to award the points to',
    points='The number of points'
)
async def award(interaction: discord.Interaction, user: discord.Member, points: int):
    msg = backend.award(user.id, user.name, points)
    await interaction.response.send_message(msg)


# @app_commands.default_permissions(manage_events=True)
@reg.command(
    name="help",
    description="get a list of all commands",
    guilds=guild_id
)
async def list_of_commands(interaction: discord.Interaction):
    commands = reg.get_commands()
    perm = interaction.user.resolved_permissions.manage_events
    output = ""
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


client.run(discord_token)
