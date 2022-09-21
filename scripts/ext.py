from pathlib import Path
import sqlite3
import sys
import pandas as pd
project_path = Path(__file__).parent

meeting_codes = ("OSDFT", "OZHIW", "WBYAG", "AWDAA")

conn = sqlite3.connect(project_path.parent.joinpath("cyberham").joinpath("db").joinpath("attendance.db"))
c = conn.cursor()


def ncl_voucher(csv):
    df = pd.read_csv(csv)
    for email in df['Username']:
        count = 0
        c.execute("SELECT user_id, name FROM users WHERE email = ?", (email, ))
        _id = c.fetchone()
        if (_id is None):
            print(f"{email} is not registered")
            continue
        c.execute(f"SELECT code FROM events WHERE attended_users LIKE '%{_id[0]}%'")
        events = c.fetchall()

        for event in events:
            if event[0] in meeting_codes:
                count += 1

        print(f"<@{_id[0]}> {_id[1]} {email} - {count}")

if __name__ == '__main__':
    if (sys.argv[1] == 'ncl'):
        ncl_voucher(sys.argv[2], sys.argv[3:])