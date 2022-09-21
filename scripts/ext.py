from pathlib import Path
import sqlite3
import sys
import pandas as pd
project_path = Path(__file__).parent

conn = sqlite3.connect(project_path.parent.joinpath("cyberham").joinpath("db").joinpath("attendance.db"))
c = conn.cursor()

def ncl_voucher(csv):
    df = pd.read_csv(csv)
    for email in df['Username']:
        count = 0
        c.execute("SELECT user_id FROM users WHERE email = ?", (email, ))
        _id = c.fetchone()
        c.execute("SELECT code FROM events WHERE attended_users LIKE ?", (f"%{_id}%", ))
        events = c.fetchall()

        for event in events:
            if event in ("OSDFT", "OZHIW", "WBYAG", "AWDAA"):
                count += 1

        print(email, count)

if __name__ == '__main__':
    if (sys.argv[1] == 'ncl'):
        ncl_voucher(sys.argv[2])