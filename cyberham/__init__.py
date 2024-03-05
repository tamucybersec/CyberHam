import tomllib
from pathlib import Path
from dataclasses import dataclass

import sqlite3

project_path = Path(__file__).parent

with open(project_path.parent.joinpath("config.toml"), "rb") as f:
    data = tomllib.load(f)

conn = sqlite3.connect(project_path.joinpath("db").joinpath("attendance.db"))
c = conn.cursor()

google_token = project_path.joinpath("secrets").joinpath("token.json")
client_secret = project_path.joinpath("secrets").joinpath(data["google"]["client_file_name"])
discord_token = data["discord"]["token"]


@dataclass
class Guild:
    id: int


guild_id = [Guild(x) for x in data["discord"]["test_guild_ids"]]
admin_channel_id = data["discord"]["admin_channel_id"]
es_api_key = data["elasticsearch"]["api_key"]
es_id = data["elasticsearch"]["id"]
es_endpoints = data["elasticsearch"]["endpoints"]
