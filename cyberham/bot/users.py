import discord
from discord import app_commands
import cyberham.backend.register as backend_register
from cyberham import guild_id
from cyberham.bot.bot import Bot
from cyberham.bot.ui import RegisterModal
from cyberham.bot.utils import valid_guild, user_profile_embed
from typing import Any


def setup_commands(bot: Bot):
    command_tree = bot.command_tree

    @command_tree.command(name="register", description="register your information here")
    async def register(interaction: discord.Interaction):
        await interaction.response.send_modal(RegisterModal(bot))

    @app_commands.checks.cooldown(3, 5 * 60)
    @command_tree.command(
        name="verify", description="verify your TAMU email", guilds=guild_id
    )
    @app_commands.describe(code="Please enter the code sent to your TAMU email")
    async def verify(interaction: discord.Interaction, code: int):
        msg: str = backend_register.verify_email(code, interaction.user.id)
        if "verified!" in msg and interaction.guild_id == 631254092332662805:
            assert interaction.guild is not None
            member = interaction.guild.get_member(interaction.user.id)
            if member is None:
                # Fallback in case member is not cached
                member = await interaction.guild.fetch_member(interaction.user.id)
            await member.add_roles(
                discord.Object(id=1015024081432743996), reason="TAMU email verified"
            )
        await interaction.response.send_message(msg, ephemeral=True)

    @verify.error
    async def on_verify_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            backend_register.remove_pending(interaction.user.id)
            await interaction.response.send_message(
                "You have verified too many times! Please contact an officer",
                ephemeral=True,
            )

    @command_tree.command(
        name="profile", description="get your current attendance info!", guilds=guild_id
    )
    async def profile(interaction: discord.Interaction):
        await user_profile_embed(interaction, interaction.user.id)

    @command_tree.command(
        name="profile_member",
        description="get the attendance info for a specific member!",
        guilds=guild_id,
    )
    @app_commands.default_permissions(manage_events=True)
    @app_commands.describe(member="The profile for which member")
    async def profile_member(interaction: discord.Interaction, member: discord.Member):
        await user_profile_embed(interaction, member.id)

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
