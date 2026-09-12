# __init__.py runs before the entry point __main__.py does
# loads values from the secrets/config*.toml files and sets up the logger

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


def load_configs(secrets_path: Path) -> Config:
    base_config_path = secrets_path / "config.toml"
    base_config = load_config(base_config_path)
    environment = base_config.get("environment", "dev")

    env_config_path = secrets_path / f"config.{environment}.toml"
    env_config = load_config(env_config_path)

    return merge_configs(base_config, env_config)


def load_google_paths(
    secrets_path: Path, data_path: Path, config: Config
) -> tuple[Path, Path]:
    token_path = data_path / "token.json"
    seed_token_path = secrets_path / "token.json"
    if not token_path.exists() and seed_token_path.exists():
        token_path.write_text(seed_token_path.read_text())
    client_secret_path = secrets_path / config["google"]["client_file_name"]
    return token_path, client_secret_path


def setup_discord_logging(data_path: Path):
    handler = logging.FileHandler(
        filename=data_path / "discord.log", encoding="utf-8", mode="w"
    )
    handler.setLevel(logging.DEBUG)
    discord_logger = logging.getLogger("discord")
    discord_logger.addHandler(handler)


def setup_module_logging(name: str, data_path: Path):
    module_logger = logging.getLogger(name)
    file_handler = logging.FileHandler(
        filename=data_path / f"{name}.log", encoding="utf-8", mode="w"
    )
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    module_logger.addHandler(file_handler)
    module_logger.addHandler(console_handler)


project_path = Path(__file__).parent
secrets_path = project_path.parent / "secrets"
config = load_configs(secrets_path)

data_path = Path(config.get("data_dir", project_path.parent)).resolve()
data_path.mkdir(parents=True, exist_ok=True)
google_token, client_secret = load_google_paths(secrets_path, data_path, config)
setup_discord_logging(data_path)
setup_module_logging(__name__, data_path)

# load various configs for export
environment = config["environment"]
website_url = config["website_url"]
dashboard_config = config["dashboard"]
discord_token: Any = config["discord"]["token"]
guild_id = [Guild(id=x) for x in config["discord"]["test_guild_ids"]]
admin_channel_id: Any = config["discord"]["admin_channel_id"]
aggie_role_id = config['discord']['aggie_role_id']
