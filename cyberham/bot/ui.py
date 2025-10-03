from typing import cast, Optional

import discord
from discord import ui
import cyberham.backend.events as backend_events
from cyberham.bot.utils import event_list_embed, handle_attend_response


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
