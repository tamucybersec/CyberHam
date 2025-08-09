from typing import Literal, Any

import discord
from discord import app_commands
import cyberham.backend.users as backend_users
from cyberham.bot.bot import Bot
from cyberham import guild_id


def setup_commands(bot: Bot):
    command_tree = bot.command_tree

    @command_tree.command(
        name="leaderboard",
        description="find the top students with the highest points",
        guilds=guild_id,
    )
    @app_commands.describe(
        sort_by="what criteria to sort by", limit="the number of results to display"
    )
    async def leaderboard(
        interaction: discord.Interaction,
        sort_by: Literal["points", "attended"],
        limit: int = 10,
    ):
        await interaction.response.defer(thinking=True)
        users = backend_users.leaderboard(sort_by, limit)
        if not users:
            await interaction.followup.send("No results for this semester yet.")
            return

        names_column = ""
        point_column = ""
        for user, criteria in users:
            names_column += f"{user["name"]}\n"
            point_column += f"{criteria}\n"
        embed = discord.Embed(
            title=f"{sort_by.capitalize()} Leaderboard", color=0xFFFFFF
        )
        embed.add_field(name="Name", value=names_column, inline=True)
        embed.add_field(name=f"{sort_by.capitalize()}", value=point_column, inline=True)
        await interaction.followup.send(embed=embed)

    @command_tree.command(
        name="leaderboard_search",
        description="find the top students with the highest points in all the events that include the search term",
        guilds=guild_id,
    )
    @app_commands.describe(activity="what activity group to search for")
    async def leaderboard_search(interaction: discord.Interaction, activity: str):
        await interaction.response.defer(thinking=True)
        leaderboard = backend_users.leaderboard_search(activity)
        if not leaderboard:
            await interaction.followup.send("No results for this semester yet.")
            return

        prev, curr = 0, 0
        leaderboard = sorted(leaderboard, key=lambda kv: (kv[1], kv[0]), reverse=True)
        embeds: list[discord.Embed] = []

        while curr < len(leaderboard):
            names_column = ""
            point_column = ""
            for name, points in leaderboard[prev:]:
                if len(names_column) + len(name) + 1 > 1024:
                    break
                names_column += name + "\n"
                point_column += f"{points}\n"
                curr += 1

            prev = curr
            embed = discord.Embed(title=f"Leaderboard for {activity}", color=0xFFFFFF)
            embed.add_field(name="Name", value=names_column, inline=True)
            embed.add_field(name=f"Attended", value=point_column, inline=True)
            embeds.append(embed)

        await interaction.followup.send(embeds=embeds)
        # await interaction.response.send_message(f"The leaderboard for {activity}")

    # satisfy type checker
    _: list[Any] = [leaderboard, leaderboard_search]
