from dataclasses import dataclass
from pathlib import Path

import sqlite3
from dotenv import dotenv_values

project_path = Path(__file__).parent

conn = sqlite3.connect(project_path.joinpath("db").joinpath("attendance.db"))
c = conn.cursor()

gmail_token = project_path.joinpath("secrets").joinpath("token.json")
client_secret = project_path.joinpath("secrets")\
    .joinpath("client_secret_712155494453-5slbl4e29ibr63ug7mcrvvr0vbcdb88c.apps.googleusercontent.com.json")

@dataclass
class guild:
    id: int

guild_id = (guild(631254092332662805), guild(805821298193465384), guild(1096793565478277256))
discord_token = dotenv_values(project_path.joinpath("secrets").joinpath(".env"))["DISCORD_TOKEN"]
