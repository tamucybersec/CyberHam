import os
import re
import json
from typing import Sequence
from datetime import datetime
from cyberham.types import TableName, Item

path = "backups"
timestamp_re = re.compile(r"^(?P<table>\w+)_(?P<ts>\d{8}_\d{6})\.json$")


def write_backup(table: TableName, data: Item | Sequence[Item]):
    if not os.path.exists(path):
        os.mkdir(path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{path}/{table}_{timestamp}.json"
    with open(filename, "w") as file:
        file.write(json.dumps(data))


def write_full_backup():
    # prevent circular import
    from cyberham.database.sqlite import SQLiteDB

    tables: list[TableName] = [
        "users",
        "events",
        "flagged",
        "attendance",
        "points",
        "tokens",
    ]

    db = SQLiteDB("cyberham.db")
    for table in tables:
        write_backup(table, db.get_all_rows(table))


def load_latest_backup(table: TableName) -> list[Item]:
    """
    Load latest backup file matching table_YYYYMMDD_HHMMSS.json in `path`.
    Fallback to table.json if none with timestamp exists.
    """

    latest_file = None
    latest_dt = None

    for filename in os.listdir(path):
        match = timestamp_re.match(filename)
        if match and match.group("table") == table:
            ts_str = match.group("ts")
            try:
                dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            except ValueError:
                continue
            if latest_dt is None or dt > latest_dt:
                latest_dt = dt
                latest_file = filename

    if latest_file is None:
        # fallback to baseline file with no timestamp
        baseline = f"{table}.json"
        baseline_path = os.path.join(path, baseline)
        if os.path.exists(baseline_path):
            latest_file = baseline

    if latest_file is None:
        return []  # no backup found

    file_path = os.path.join(path, latest_file)
    with open(file_path, "r") as f:
        data: list[Item] = json.load(f)

    return data
