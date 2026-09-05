from typing import cast, Optional, Any
import re
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
        
class RSVPButton(ui.DynamicItem[ui.Button[Any]], template=r'rsvp:(?P<s>[1-4]):(?P<a>[^:]+):(?P<c>[^:]+):(?P<d>[^:]+):(?P<e>[^:]+):(?P<l>.+)'):
    def __init__(self, rsvplabel: str, rsvpstyle: discord.ButtonStyle, rsvpemoji: str, action: str, code: str, date: str):
        custom_id = f"rsvp:{rsvpstyle.value}:{action}:{code}:{date}:{rsvpemoji}:{rsvplabel}"
        button: ui.Button[Any]=ui.Button(
            label=rsvplabel,
            custom_id=custom_id,
            style=rsvpstyle,
            emoji=rsvpemoji
        )
        super().__init__(button)
        self.action=action
        self.code=code
        self.date=date

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: ui.Item[Any], match: re.Match[str]):
        return cls(rsvplabel=match.group('l'),
            rsvpstyle=discord.ButtonStyle(int(match.group('s'))),
            rsvpemoji=match.group('e'),
            action=match.group('a'),
            code=match.group('c'),
            date=match.group('d'))
    
    async def callback(self, interaction: discord.Interaction):
        if not self.custom_id:
            return
        # _, _, _,action, code, date = self.custom_id.split(":")
        
        response_num = {
            "yes":0,
            "no":1,
            "maybe":2
        }
        msg = backend_events.rsvp_event(uid=str(interaction.user.id), event=self.code, response=response_num[self.action], date=self.date)
        await interaction.response.send_message(msg, ephemeral=True)
        

class RSVPOptions(discord.ui.View):
    def __init__(self, code: str, date: str):
        super().__init__(timeout=None)
        self.add_item(RSVPButton("Yes", discord.ButtonStyle.green, "✅", "yes", code, date))
        self.add_item(RSVPButton("No", discord.ButtonStyle.red, "✖️", "no", code, date))
        self.add_item(RSVPButton("Maybe", discord.ButtonStyle.gray, "❓", "maybe", code, date))

