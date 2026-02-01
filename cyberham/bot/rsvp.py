from typing import cast, Any
import discord
from discord import app_commands
from cyberham.bot.ui import RSVPOptions
from cyberham import guild_id
import cyberham.backend.events as backend_events
from cyberham.bot.bot import Bot
from cyberham.bot.constants import activity_group_channels
from cyberham.utils.date import validate_date

def setup_commands(bot:Bot):
    command_tree=bot.command_tree

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="generate_rsvp_form",
        description="(unstable: breaks on server restart) generates RSVP poll for a given event code",
        guilds=guild_id,
    )
    @app_commands.describe(
        code="Enter the event code",
        date="(Optional) Enter a new date for the RSVP form to expire in mm/dd/yyyy or mm/dd/yy format"
    )
    async def generate_RSVP_form(interaction:discord.Interaction,code: str="", date: str=""):
        msg,event=backend_events.find_event(code)[:2]
        if event is None:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        if date=="":
            date=event["date"]
        elif not validate_date(date):
            await interaction.response.send_message("Invalid date! Please return a valid date in the format mm/dd/yy or mm/dd/yyyy.", ephemeral=True)
            return
        
        #Set up channel to send RSVP to
        if environment == "dev":
            channel_id = "Tech Committee"
        elif (event["category"] in activity_group_channels):
            channel_id = event["category"]
        else:
            channel_id = "Announcements"
        channel=cast(discord.TextChannel,await bot.fetch_channel(activity_group_channels[channel_id]))
        question=f"{event["category"]}: Do you plan to attend **{event["name"]}** on **{event["date"]}**?"
        buttons = RSVPOptions(code=code, date=date)
        await channel.send(question, view=buttons)
        await interaction.response.send_message("RSVP question sent: "+question, ephemeral=True)

    @app_commands.default_permissions(manage_events=True)
    @command_tree.command(
        name="count_rsvp",
        description="generates RSVP response count for a given event code",
        guilds=guild_id,
    )
    async def count_rsvp(interaction:discord.Interaction,code:str=""):
        await interaction.response.send_message(backend_events.count_rsvp_event(code),ephemeral=True)
        
    # satisfy type checker
    _: list[Any] = [generate_RSVP_form, count_rsvp]
    
    




        
        

        
        
        

