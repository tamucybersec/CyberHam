import tomllib
import logging
from pathlib import Path
from dataclasses import dataclass

import sqlite3

project_path = Path(__file__).parent

with open(project_path.parent.joinpath("config.toml"), "rb") as f:
    data = tomllib.load(f)

conn = sqlite3.connect(project_path.joinpath("db").joinpath("attendance.db"))
c = conn.cursor()

google_token = project_path.joinpath("secrets").joinpath("token.json")
client_secret = project_path.joinpath("secrets").joinpath(data["google_client"])
discord_token = data["discord_token"]

@dataclass
class Guild:
    id: int


guild_id = [Guild(x) for x in data["test_guild_ids"]]
admin_channel_id = data["admin_channel_id"]

# config discord logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setLevel(logging.DEBUG)
logger = logging.getLogger('discord')
logger.addHandler(handler)

# config current module logging
logger = logging.getLogger(__name__)
handler = logging.FileHandler(filename=f'{__name__}.log', encoding='utf-8', mode='w')
handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.addHandler(console_handler)
