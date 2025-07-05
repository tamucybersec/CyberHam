from typing import cast, Optional

import discord
from discord import ui
import cyberham.backend.events as backend_events
import cyberham.backend.register as backend_register
from cyberham import admin_channel_id
from cyberham.bot.bot import Bot
from cyberham.bot.utils import valid_guild, event_list_embed, handle_attend_response


class PageDisplay(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.response = None
        self.page = 0

    @discord.ui.button(
        style=discord.ButtonStyle.primary, custom_id="el_left", emoji="◀"
    )
    async def left(
        self, interaction: discord.Interaction, _: discord.ui.Button[discord.ui.View]
    ):
        if self.page > 0:
            self.page -= 1
        else:
            await interaction.response.defer()
            return

        await self.change_page(interaction)

    @discord.ui.button(
        style=discord.ButtonStyle.primary, custom_id="el_next", emoji="▶"
    )
    async def next(
        self, interaction: discord.Interaction, _: discord.ui.Button[discord.ui.View]
    ):
        if self.page < backend_events.event_count() // 5:
            self.page += 1
        await self.change_page(interaction)

    async def change_page(self, interaction: discord.Interaction):
        embed = event_list_embed(self.page)
        if embed is None:
            await interaction.response.defer()
            return
        await interaction.response.edit_message(embed=embed, view=self)


class RegisterModal(ui.Modal, title="Register"):
    name = ui.TextInput["RegisterModal"](
        label="name", placeholder="please enter your full name/names you go by"
    )
    grad_year = ui.TextInput["RegisterModal"](
        label="grad_year", placeholder="your graduation year (yyyy), e.g. 2024"
    )
    email = ui.TextInput["RegisterModal"](label="email", placeholder="TAMU email")

    bot: Bot

    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        if not await valid_guild(interaction):
            return
        assert interaction.guild is not None

        name = self.name.value
        grad_year = self.grad_year.value
        email = self.email.value
        try:
            msg: str = backend_register.legacy_register(
                name,
                grad_year,
                email,
                str(interaction.user.id),
            )
        except:
            channel = cast(discord.TextChannel, self.bot.get_channel(admin_channel_id))
            await channel.send(
                f"{interaction.user.mention} registration attempt, update token"
            )
            self.bot.logger.debug(name, grad_year, email, interaction.user.name)
            msg = "The verification code failed to send, an officer has been notified and will contact you soon"
        await interaction.response.send_message(msg, ephemeral=True)


class AttendModal(ui.Modal, title="Attend"):
    code = ui.TextInput["AttendModal"](label="code")

    async def on_submit(self, interaction: discord.Interaction):
        await handle_attend_response(interaction, self.code.value)


class EditModal(discord.ui.Modal, title="Edit a Message"):
    answer = discord.ui.TextInput["EditModal"](
        label="Message content", style=discord.TextStyle.paragraph, max_length=2000
    )

    def __init__(self, message: Optional[discord.Message] = None):
        super().__init__()
        self.message = message

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.message is None:
            await interaction.response.send_message(
                f"Howdy! The message has been sent.", ephemeral=True
            )
            channel = cast(discord.TextChannel, interaction.channel)
            await channel.send(f"{self.answer}")
        else:
            await interaction.response.send_message(
                f"Howdy! The message has been updated.", ephemeral=True
            )
            await self.message.edit(content=f"{self.answer}")
