import discord
import cyberham.backend.events as backend_events
import cyberham.backend.users as backend_users
from cyberham.database.queries import points_for_user, attendance_for_user, attendance_for_user_specific_category
from cyberham.utils.date import current_semester, current_year


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
    num_attendees_total: int = 0,
    num_attendees_category: int = 0,
    category: str = ""
):
    embed = discord.Embed(title="Event Information", color=0xFFFFFF)
    embed.add_field(name="Name", value=name, inline=False)
    embed.add_field(name="Points", value=points, inline=False)
    embed.add_field(name="Code", value=code, inline=False)
    embed.add_field(name="Date", value=date, inline=False)

    # helps handle the case of whether this is to show an event's total attendance or a person's attendance
    if category != "":
        curr_semester = current_semester().title()
        curr_year = current_year()

        embed.add_field(name=f"Overall Attendance Count ({curr_semester} {curr_year})"
                        , value=num_attendees_total, inline=False)
        embed.add_field(name=f"{category} Attendance Count ({curr_semester} {curr_year})"
                        , value=num_attendees_category, inline=False)
    else:
        embed.add_field(name="Attendance count", value=num_attendees_total, inline=False)

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


async def user_profile_embed(interaction: discord.Interaction, user_id: str):
    msg, user = backend_users.profile(user_id)
    if user is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    points = points_for_user(user["user_id"])
    attendance = attendance_for_user(user["user_id"])

    embed = discord.Embed(title="Profile", color=0xFFFFFF)
    embed.add_field(name="Name", value=user["name"], inline=False)
    embed.add_field(name="Points", value=points, inline=False)
    embed.add_field(name="Attended Events", value=attendance, inline=False)
    if user["grad_year"] > 0:
        embed.add_field(name="Graduation Year", value=user["grad_year"], inline=False)
    if user["email"]:
        embed.add_field(name="TAMU Email", value=user["email"], inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def handle_attend_response(interaction: discord.Interaction, code: str):
    msg, event = backend_events.attend_event(code, str(interaction.user.id))
    if event is None:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    # gets the attendance for user for whole semester and the certain category
    total_semester_attendance = attendance_for_user(str(interaction.user.id))
    category_semester_attendnce = attendance_for_user_specific_category(str(interaction.user.id), event["category"])

    embed = event_info(event["name"], event["points"], event["date"], code,
                       total_semester_attendance, category_semester_attendnce, event["category"])
    await interaction.response.send_message(msg, embed=embed, ephemeral=True)
