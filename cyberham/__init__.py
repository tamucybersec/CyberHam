import tomllib
import logging

from pathlib import Path
from dataclasses import dataclass

project_path = Path(__file__).parent

# load config.toml
with open(project_path.parent.joinpath("config.toml"), "rb") as f:
    data = tomllib.load(f)

# loading tokens
google_token = project_path.joinpath("secrets").joinpath("token.json")
client_secret = project_path.joinpath("secrets").joinpath(
    data["google"]["google_client"]
)
discord_token = data["discord"]["token"]
dynamo_keys = data["dynamo"]
encryption_keys = data["encryption"]
dashboard_credentials = data["dashboard"]

# discord outputs configs
@dataclass
class Guild:
    id: int


guild_id = [Guild(id=x) for x in data["discord"]["test_guild_ids"]]
admin_channel_id = data["discord"]["admin_channel_id"]

# config discord logging
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setLevel(logging.DEBUG)
logger = logging.getLogger("discord")
logger.addHandler(handler)

# config current module logging
logger = logging.getLogger(__name__)
handler = logging.FileHandler(filename=f"{__name__}.log", encoding="utf-8", mode="w")
handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.addHandler(console_handler)
