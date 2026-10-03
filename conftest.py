"""Configure isolated test data before pytest imports the cyberham package."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def pytest_configure(config: pytest.Config) -> None:
    # A fixture in cyberham/tests is too late: importing the parent package
    # loads configuration and initializes the database before fixtures run.
    temporary = TemporaryDirectory(prefix="cyberham-tests-")
    config.add_cleanup(temporary.cleanup)
    root = Path(temporary.name)
    secrets = root / "secrets"
    secrets.mkdir()
    data = root / "data"
    (secrets / "config.toml").write_text(
        f"""environment = "dev"
website_url = "http://localhost:3000"
data_dir = {json.dumps(str(data))}

[google]
client_file_name = "unused-test-client.json"

[dashboard]
host = "127.0.0.1"
port = 5183

[discord]
token = "test-only"
test_guild_ids = []
admin_channel_id = 0
aggie_role_id = 0

[ipcx]
secret_key = "test-only"
port = 19876
""",
        encoding="utf-8",
    )
    (secrets / "config.dev.toml").write_text("", encoding="utf-8")
    # Google initializes its client on import. A synthetic unexpired token
    # prevents it from starting OAuth or reading a developer's credentials.
    # API calls are mocked by the tests; this token cannot authenticate.
    (secrets / "token.json").write_text(
        json.dumps(
            {
                "token": "test-only",
                "refresh_token": "test-only",
                "client_id": "test-only",
                "client_secret": "test-only",
                "expiry": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    env = pytest.MonkeyPatch()
    config.add_cleanup(env.undo)
    env.setenv("CYBERHAM_SECRETS_DIR", str(secrets))
    env.setenv("CYBERHAM_ENV", "dev")
    env.delenv("GOATCOUNTER_URL", raising=False)
    env.delenv("GOATCOUNTER_API_TOKEN", raising=False)
