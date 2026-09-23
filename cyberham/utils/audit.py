# Here is where the logs are accessed and logged from the dashboard api, which records the following:
# - admin portal logins
# - wrong login attempts
# - under-priviledged api key access attempt

# the information is written as <data_dir>/logs/access-YYYY-MM.txt. A new file is started
# each month and only the current and previous month are kept (which then cycle)
import hashlib
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi.requests import Request

from cyberham import data_path
from cyberham.database.typeddb import tokensdb

LOG_DIR = data_path / "logs"
KEEP_MONTHS = 2

# inherits from FileHandler
class MonthlyFileHandler(logging.FileHandler):
    def __init__(self, directory: Path, prefix: str):
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory
        self.prefix = prefix
        self.month = datetime.now().strftime("%Y-%m")
        super().__init__(self._path(), encoding="utf-8", mode="a", delay=True)

    # joining paths together
    def _path(self) -> Path:
        return self.directory / f"{self.prefix}-{self.month}.txt"

    # if a new month has started, then switch to that months file (runs every log)
    def emit(self, record: logging.LogRecord) -> None:
        month = datetime.now().strftime("%Y-%m")
        
        if month != self.month:
            self.close()
            self.month = month
            self.baseFilename = str(self._path())
            # YYYY-MM names sort chronologically
            old_files = sorted(self.directory.glob(f"{self.prefix}-*.txt"))
            for old_file in old_files[:-KEEP_MONTHS]:
                old_file.unlink(missing_ok=True)
        super().emit(record) # runs pythons logging library



access_logger = logging.getLogger("cyberham.access")
access_logger.setLevel(logging.INFO) # minimum handler pass-through 

# makes sure that we dont duplicate every log line
if not access_logger.handlers:
    # currently only logging for valid login attempts (thus "access")
    handler = MonthlyFileHandler(LOG_DIR, "access")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    access_logger.addHandler(handler)


def _describe_key(token: str) -> str:
    # hashes/encrypts the name of the token used (in case logs get leaked)
    fingerprint = hashlib.sha256(token.encode()).hexdigest()[:8]
    try:
        # attempts to find token in db
        record = tokensdb.get((token,))
    except sqlite3.Error:
        # logging must never be the reason a request fails
        return f"lookup failed #{fingerprint}"
    name = record["name"] if record is not None else "unknown key"
    return f"{name} #{fingerprint}"


def _client_ip(request: Request) -> str:
    # behind a proxy the real client is in x-forwarded-for; keeps the whole chain
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def log_access(event: str, token: str, request: Request, success: bool) -> None:
    message = (
        f"{event} | key={_describe_key(token)} | ip={_client_ip(request)}"
        f" | {request.method} {request.url.path}"
    )
    access_logger.log(logging.INFO if success else logging.WARNING, message)
