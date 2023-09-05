import tomllib
from pathlib import Path
from dataclasses import dataclass

import sqlite3

project_path = Path(__file__).parent

with open(project_path.parent.joinpath("config.toml"), "rb") as f:
    data = tomllib.load(f)

conn = sqlite3.connect(project_path.joinpath("db").joinpath("attendance.db"))
c = conn.cursor()

gmail_token = project_path.joinpath("secrets").joinpath("token.json")
client_secret = project_path.joinpath("secrets").joinpath(data["google_client"])
discord_token = data["discord_token"]


@dataclass
class Guild:
    id: int


guild_id = [Guild(x) for x in data["test_guild_ids"]]
