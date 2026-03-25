import discord
from discord import app_commands
import cyberham.backend.register as backend_register
from cyberham import guild_id, admin_channel_id, server_interaction_guild_id, aggie_role_id
from cyberham.bot.bot import Bot
from cyberham.bot.utils import valid_guild, user_profile_embed
from cyberham.database.typeddb import usersdb
from typing import Any

def setup_commands(bot: Bot):
    command_tree = bot.command_tree

    @command_tree.command(
        name="register",
        description="register or update your information here",
        guilds=guild_id,
    )
    async def register(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        url = backend_register.generate_registration_url(user_id)
        button = discord.ui.Button[discord.ui.View](label="Register", url=url)
        view = discord.ui.View()
        view.add_item(button)
        await interaction.response.send_message(
            "Below is your personal registration link. Do not share this with others! It is valid for the next hour.",
            view=view,
            ephemeral=True,
        )

    @app_commands.checks.cooldown(3, 5 * 60)
    @command_tree.command(
        name="verify", description="verify your TAMU email", guilds=guild_id
    )
    @app_commands.describe(code="Please enter the code sent to your TAMU email")
    async def verify(interaction: discord.Interaction, code: int):
        msg: str = backend_register.verify_email(code, str(interaction.user.id))

        if "verified!" in msg and interaction.guild_id == server_interaction_guild_id:
            assert interaction.guild is not None
            member = interaction.guild.get_member(interaction.user.id)
            if member is None:
                # Fallback in case member is not cached
                member = await interaction.guild.fetch_member(interaction.user.id)

            user = usersdb.get((interaction.user.id,))

            if user["email"].endswith("tamu.edu"):
                await member.add_roles(
                    discord.Object(id=aggie_role_id), reason="TAMU email verified"
                )

        await interaction.response.send_message(msg, ephemeral=True)

    @verify.error
    async def on_verify_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            backend_register.remove_pending(str(interaction.user.id))
            await interaction.response.send_message(
                "You have verified too many times! Please contact an officer",
                ephemeral=True,
            )

    @command_tree.command(
        name="profile", description="get your current attendance info!", guilds=guild_id
    )
    async def profile(interaction: discord.Interaction):
        await user_profile_embed(interaction, str(interaction.user.id))

    @command_tree.command(
        name="profile_member",
        description="get the attendance info for a specific member!",
        guilds=guild_id,
    )
    @app_commands.default_permissions(manage_events=True)
    @app_commands.describe(member="The profile for which member")
    async def profile_member(interaction: discord.Interaction, member: discord.Member):
        await user_profile_embed(interaction, str(member.id))

    @command_tree.command(
        name="size", description="find the number of human members", guilds=guild_id
    )
    async def size(interaction: discord.Interaction):
        if not await valid_guild(interaction):
            return
        assert interaction.guild is not None

        count = 0
        for member in interaction.guild.members:
            if not member.bot:
                count += 1
        await interaction.response.send_message(
            f"There are {count} humans in the server."
        )

    @command_tree.command(
        name="help", description="get a list of all commands", guilds=guild_id
    )
    async def list_of_commands(interaction: discord.Interaction):
        commands = command_tree.get_commands()

        if (
            isinstance(interaction.user, discord.Member)
            and interaction.user.resolved_permissions
        ):
            perm: bool = interaction.user.resolved_permissions.manage_events
        else:
            perm = False

        output: str = ""

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

    @app_commands.checks.cooldown(3, 5 * 60)
    @command_tree.command(
        name="remove_aggie_role", description="remove Aggie role for all verified users with a non tamu.edu email",
        guilds=guild_id
    )
    async def remove_non_aggie_roles(interaction: discord.Interaction):
        if interaction.channel.id != admin_channel_id:
            await interaction.response.send_message("You do not have the permissions "
                                                    "or are in the wrong channel to run this command.")
            return

        for dict in usersdb.get_all():
            if not dict['email'].endswith("tamu.edu"):
                member = interaction.guild.get_member(dict['user_id'])

                if member is None:
                    # Fallback in case member is not cached
                    member = await interaction.guild.fetch_member(dict['user_id'])

                await member.remove_roles(
                    discord.Object(1486203798815903819),
                    reason="email used for verification is not an tamu.edu email"
                )

        await interaction.response.send_message("All previously verified members without a tamu.edu email do not have an Aggie role!")

    # satisfy type checker
    _: list[Any] = [
        register,
        verify,
        on_verify_error,
        profile,
        profile_member,
        size,
        list_of_commands,
    ]
