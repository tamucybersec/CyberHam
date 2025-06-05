# __init__.py runs before the entry point __main__.py does
# loads values from the config.toml and sets up the logger

import tomllib
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any

type Config = dict[str, Any]


# discord outputs configs
@dataclass
class Guild:
    id: int


def load_config(path: Path) -> Config:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_google_paths(project_path: Path, config: Config) -> tuple[Path, Path]:
    secrets_path = project_path / "secrets"
    token_path = secrets_path / "token.json"
    client_secret_path = secrets_path / config["google"]["google_client"]
    return token_path, client_secret_path


def setup_discord_logging():
    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
    handler.setLevel(logging.DEBUG)
    discord_logger = logging.getLogger("discord")
    discord_logger.addHandler(handler)


def setup_module_logging(name: str):
    module_logger = logging.getLogger(name)
    file_handler = logging.FileHandler(
        filename=f"{name}.log", encoding="utf-8", mode="w"
    )
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    module_logger.addHandler(file_handler)
    module_logger.addHandler(console_handler)


project_path = Path(__file__).parent
config = load_config(project_path.parent / "config.toml")
google_token, client_secret = load_google_paths(project_path, config)
setup_discord_logging()
setup_module_logging(__name__)

# load various configs for export
discord_token: Any = config["discord"]["token"]
encryption_keys: Any = config["encryption"]
dashboard_credentials: Any = config["dashboard"]
guild_id = [Guild(id=x) for x in config["discord"]["test_guild_ids"]]
admin_channel_id: Any = config["discord"]["admin_channel_id"]
