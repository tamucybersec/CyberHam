# __init__.py runs before the entry point __main__.py does
# loads values from the config.toml and sets up the logger

import tomllib
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any, cast

type Config = dict[str, Any]


# discord outputs configs
@dataclass
class Guild:
    id: int


def load_config(path: Path) -> Config:
    with open(path, "rb") as f:
        return tomllib.load(f)


def merge_configs(base: Config, override: Config) -> Config:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            merge_configs(base[key], cast(Config, value))
        else:
            base[key] = value
    return base


def load_configs(root: Path) -> Config:
    base_config_path = root / "config.toml"
    base_config = load_config(base_config_path)
    environment = base_config.get("environment", "dev")

    env_config_path = root / f"config.{environment}.toml"
    env_config = load_config(env_config_path)

    merged = merge_configs(base_config, env_config)

    local_config_path = root / "config.local.toml"
    if local_config_path.exists():
        local_config = load_config(local_config_path)
        merged = merge_configs(merged, local_config)

    return merged


def load_google_paths(project_path: Path, config: Config) -> tuple[Path, Path]:
    secrets_path = project_path / "../secrets"
    token_path = secrets_path / "token.json"
    client_secret_path = secrets_path / config["google"]["client_file_name"]
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
config = load_configs(project_path.parent)
google_token, client_secret = load_google_paths(project_path, config)
setup_discord_logging()
setup_module_logging(__name__)

# load various configs for export
environment = config["environment"]
website_url = config["website_url"]
dashboard_config = config["dashboard"]
discord_token: Any = config["discord"]["token"]
guild_id = [Guild(id=x) for x in config["discord"]["test_guild_ids"]]
admin_channel_id: Any = config["discord"]["admin_channel_id"]
db_path: str = config.get("database", {}).get("path", "cyberham.db")
