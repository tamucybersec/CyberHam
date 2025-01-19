import tomllib
import logging

# from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

import sqlite3

project_path = Path(__file__).parent

# load config.toml
with open(project_path.parent.joinpath("config.toml"), "rb") as f:
    data = tomllib.load(f)

# connecting to local sqlite db
conn = sqlite3.connect(project_path.joinpath("db").joinpath("attendance.db"))
c = conn.cursor()

# loading tokens
google_token = project_path.joinpath("secrets").joinpath("token.json")
client_secret = project_path.joinpath("secrets").joinpath(
    data["google"]["google_client"]
)
discord_token = data["discord"]["token"]
dynamo_keys = data["dynamo"]


# discord outputs configs
@dataclass
class Guild:
    id: int


guild_id = [Guild(x) for x in data["discord"]["test_guild_ids"]]
admin_channel_id = data["discord"]["admin_channel_id"]


# # elasticsearch configs
# @dataclass
# class ElasticsearchConfig:
#     api_key: str
#     id: str
#     endpoints: str
#     index_postfix: str


# es_data = data["elasticsearch"]

# # Check if 'index_postfix' exists in Elasticsearch data
# if "index_postfix" in es_data:
#     es_index_postfix = es_data["index_postfix"]
# else:
#     # If 'index_postfix' does not exist, use the current year
#     es_index_postfix = str(datetime.now().year)

# # Create Elasticsearch configuration
# es_conf = ElasticsearchConfig(
#     api_key=es_data["api_key"],
#     id=es_data["id"],
#     endpoints=es_data["endpoints"],
#     index_postfix=es_index_postfix
# )


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
