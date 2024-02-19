from typing import Literal
from pytz import timezone

import discord
from discord import app_commands,ui

import cyberham.backend as backend
from cyberham import guild_id, discord_token

"""
Define Bot Attributes
"""


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents(guilds=True, members=True, messages=True, guild_scheduled_events=True))
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        for g in guild_id:
            await reg.sync(guild=g)
            print("synced server ", g.id)
        self.synced = True
        print("bot online")

    async def on_scheduled_event_create(self, event):
        # voice channel events do not trigger this
        points = 50
        time = event.start_time.astimezone(timezone('US/Central'))

        code = backend.create_event(event.name, points, time.strftime("%m/%d/%Y"), "", event.creator_id)
        embed = event_info(event.name, points, time.strftime("%m/%d/%Y"), code, "")
        await self.get_channel(1014740464601153536).send(f"The code is `{code}`", embed=embed)


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
        if self.page < len(backend.event_list()) // 5:
            self.page += 1
        embed = event_list_embed(self.page)
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

class AttendModal(ui.Modal, title="Attend"):
    code = ui.TextInput(label="code")
    async def on_submit(self, interaction: discord.Interaction):
        code = self.code.value
        msg, data = backend.attend_event(code, interaction.user.id, interaction.user.name)
        if data is None:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        name, points, date, resources = data
        embed = event_info(name, points, date, code, resources)
        await interaction.response.send_message(msg, embed=embed, ephemeral=True)
        
@app_commands.checks.cooldown(5, 30 * 60)
@reg.command(
    name="attend",
    description="register at the event you are attending for rewards and resources",
    guilds=guild_id
)
@app_commands.describe(code='(optional) The code of the event given by the presenter')
async def attend(interaction: discord.Interaction, code: str = ""):
    if code == "":
        await interaction.response.send_modal(AttendModal())
        return
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
    name="leaderboard_search",
    description="find the top students with the highest points in all the events that include the search term",
    guilds=guild_id
)
@app_commands.describe(
    activity='what activity group to search for'
)
async def leaderboard_search(
        interaction: discord.Interaction, activity: str
):
    lb = backend.leaderboard_search(activity)
    if not lb:
        await interaction.response.send_message("There are no registered users yet")
        return
    prev, curr = 0, 0
    lb = sorted(lb, key=lambda kv: (kv[1], kv[0]), reverse=True)
    embeds = []
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
async def profile_member(interaction: discord.Interaction, member: discord.Member):
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


class EditModal(discord.ui.Modal, title='Edit a Message'):
    answer = discord.ui.TextInput(label='Message content', style=discord.TextStyle.paragraph, max_length=2000)

    def __init__(self, message: discord.Message = None):
        super().__init__()
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        if self.message is None:
            await interaction.response.send_message(f'Howdy! The message has been sent.', ephemeral=True)
            await interaction.channel.send(f'{self.answer}')
        else:
            await interaction.response.send_message(f'Howdy! The message has been updated.', ephemeral=True)
            await self.message.edit(content=f'{self.answer}')


@app_commands.default_permissions(manage_events=True)
@reg.context_menu(
    name="Edit message",
    guilds=guild_id
)
async def edit_message(interaction: discord.Interaction, message: discord.Message) -> None:
    modal = EditModal(message)
    await interaction.response.send_modal(modal)


@app_commands.default_permissions(manage_events=True)
@reg.command(
    name="send_editable_message",
    description="send a message that will be editable by user with permission configured in integrations",
    guilds=guild_id
)
async def send_editable_message(interaction: discord.Interaction) -> None:
    modal = EditModal()
    await interaction.response.send_modal(modal)


client.run(discord_token)
