import discord
import cyberham.backend.events as backend_events


async def valid_guild(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Error: No GuildID found in discord interaction."
        )
        return False
    return True


def event_info(
    name: str,
    points: int,
    date: str,
    code: str,
    resources: str,
    attendees: str,
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
    events = backend_events.event_list()
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


async def handle_attend_response(interaction: discord.Interaction, code: str):
    msg, event = backend_events.attend_event(code, interaction.user.id)
    if event is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    embed = event_info(
        event["name"], event["points"], event["date"], code, event["resources"], ""
    )
    await interaction.response.send_message(msg, embed=embed, ephemeral=True)
