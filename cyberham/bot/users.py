import discord
from discord import app_commands
import cyberham.backend.register as backend_register
from cyberham import guild_id, admin_channel_id, aggie_role_id
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

        if "verified!" in msg and interaction.guild_id == guild_id[0].id:
            assert interaction.guild is not None
            member = interaction.guild.get_member(interaction.user.id)
            if member is None:
                # Fallback in case member is not cached
                member = await interaction.guild.fetch_member(interaction.user.id)

            user = usersdb.get((str(interaction.user.id),))

            if user is not None and user["email"].endswith("tamu.edu"):
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
        name="refresh_aggie_role", description="refresh aggie role grants for all members",
        guilds=guild_id
    )
    async def refresh_non_aggie_roles(interaction: discord.Interaction):
        if interaction.channel is not None and interaction.channel.id != admin_channel_id:
            await interaction.response.send_message("You do not have the permissions "
                                                    "or are in the wrong channel to run this command.")
            return
        if interaction.guild is None:
            await interaction.response.send_message("This command must be run in a server.")
            return
        await interaction.response.defer()

        for dict in usersdb.get_all():
            member = interaction.guild.get_member(int(dict['user_id']))

            if member is None:
                try:
                    # Fallback in case member is not cached
                    member = await interaction.guild.fetch_member(int(dict['user_id']))
                except discord.NotFound:
                    # user is no longer in the server
                    continue

            has_role = any(role.id == aggie_role_id for role in member.roles)
            is_tamu = dict['verified'] and dict['email'].endswith("tamu.edu")

            if is_tamu and not has_role:
                await member.add_roles(
                    discord.Object(id=aggie_role_id),
                    reason="verified with a tamu.edu email"
                )
            elif not is_tamu and has_role:
                await member.remove_roles(
                    discord.Object(id=aggie_role_id),
                    reason="email used for verification is not an tamu.edu email"
                )

        await interaction.followup.send("Aggie roles have been refreshed for all members!")

    # satisfy type checker
    _: list[Any] = [
        register,
        verify,
        on_verify_error,
        profile,
        profile_member,
        size,
        list_of_commands,
        refresh_non_aggie_roles
    ]
