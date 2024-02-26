import random
import string

from typing import Literal
from datetime import datetime

from cyberham import conn, c
from cyberham.google_apis import GoogleClient

pending_emails = {}
google_client = GoogleClient()

def init_db():
    # users: user_id, name, points, attended_dates, grad_year, tamu_email
    c.execute(
        "CREATE TABLE IF NOT EXISTS "
        "users(user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER, attended INTEGER, grad_year INTEGER, email TEXT)"
    )
    # events: name, code, points, date (mm/dd/yy), resources, attended_users
    c.execute(
        "CREATE TABLE IF NOT EXISTS "
        "events(name TEXT, code TEXT PRIMARY KEY, points INTEGER, date TEXT, resources TEXT, attended_users TEXT)"
    )
    # flagged: user_id, offences
    c.execute(
        "CREATE TABLE IF NOT EXISTS "
        "flagged(user_id INTEGER PRIMARY KEY, offences INTEGER)"
    )
    conn.commit()


def create_event(name: str, points: int, date: str, resources: str, user_id: int):
    code = ""
    code_list = [0]
    while code_list is not None:
        code = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
        c.execute("SELECT name FROM events WHERE code = ?", (code,))
        code_list = c.fetchone()  # returns tuple of one if exists otherwise none

    c.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
        (name, code, points, date, resources, f"{user_id}"),
    )
    c.execute(
        "UPDATE users SET points = points + ? WHERE user_id = ?",
        (points, user_id),
    )
    c.execute(
        "UPDATE users SET attended = attended + 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    return code


def attend_event(code: str, user_id: int, user_name: str):
    code = code.upper()
    c.execute("SELECT grad_year FROM users WHERE user_id = ?", (user_id,))

    grad_year = c.fetchone()
    if grad_year is None or grad_year[0] == 0:
        prompt = "Please use /register to make a profile!"
        c.execute(
            "INSERT OR IGNORE INTO users VALUES (?, ?, 0, 0, 0, '')",
            (user_id, user_name),
        )
        conn.commit()
    else:
        prompt = ""

    c.execute("SELECT * FROM events WHERE code = ?", (code,))
    temp = c.fetchone()
    if temp is None:
        return f"{code} does not exist!", None

    name, _, points, date, resources, attended_users = temp
    if f'{user_id}' in attended_users.split():
        return f"You have already redeemed {code}!", None

    c.execute(
        "UPDATE users SET points = points + ? WHERE user_id = ?",
        (points, user_id),
    )
    c.execute(
        "UPDATE users SET attended = attended + 1 WHERE user_id = ?",
        (user_id,),
    )
    c.execute(
        "UPDATE events SET attended_users = attended_users || ? WHERE code = ?",
        (f" {user_id}", code),
    )
    conn.commit()
    return f"Successfully registered for {code}! {prompt}", (
        name,
        points,
        date,
        resources,
    )


def leaderboard(axis: Literal["points", "attended"], lim: int = 10):
    if axis == "points":
        c.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT ?", (lim,))
    else:
        c.execute(
            "SELECT name, attended FROM users ORDER BY attended DESC LIMIT ?", (lim,)
        )
    return c.fetchall()


def leaderboard_search(activity: str):
    c.execute("SELECT name, attended_users FROM events;")
    counts = {}
    for name, attended_users in c.fetchall():
        if activity.lower() not in name.lower():
            continue
        for attended_user_id in attended_users.split(' '):
            key = int(attended_user_id)
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1

    list_with_names = []
    for attended_user_id, count in counts.items():
        c.execute(
            "SELECT name FROM users WHERE user_id = ?", (attended_user_id, )
        )
        list_with_names.append((c.fetchone()[0], count))

    return list_with_names


def register(name: str, grad_year: int, email: str, user_id: int, user_name: str, guild_id: int):
    # if c.execute("SELECT name FROM users WHERE user_id = ?", (user_id,)) is not None:
    #     return "You have already registered"

    c.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?, 0, 0, 0, '')",
        (user_id, user_name),
    )
    conn.commit()

    # assuming our users are standard mortals of the non-time-travelling variety
    if not datetime.now().year - 100 < grad_year < datetime.now().year + 5:
        return "Please set your graduation year in the format YYYY (e.g. 2022)"

    email = email.lower()
    if (
            "," in email
            or ";" in email
            or email.count("@") != 1
            or not email.endswith("tamu.edu")
    ):
        return "Please set a proper TAMU email address"

    ask_to_verify = register_email(user_id, email, guild_id)

    c.execute(
        "UPDATE users SET name = ?, grad_year = ? WHERE user_id = ?",
        (name, grad_year, user_id),
    )
    conn.commit()
    return f"You have successfully updated your profile! {ask_to_verify}"


def register_email(user_id, email, guild_id):
    c.execute("SELECT email FROM users WHERE user_id = ?", (user_id,))
    temp = c.fetchone()
    if temp is not None and temp[0] == email:
        return ""

    if user_id in pending_emails:
        c.execute("INSERT OR IGNORE INTO flagged VALUES (?, 0)", (user_id,))
        c.execute("UPDATE flagged SET offences = offences + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        c.execute("SELECT offences FROM flagged WHERE user_id = ?", (user_id,))
        flagged = c.fetchone()[0]
        if flagged >= 3:
            return "Too many failed attempts to email verification, please contact an officer"

    c.execute("SELECT user_id FROM users WHERE email = ?", (email,))
    temp = c.fetchone()
    if temp is not None:
        c.execute("UPDATE flagged SET offences = offences + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return "This email has already been registered"

    verification = EmailPending(
        user_id, email, random.randint(1000, 10000), datetime.now()
    )
    pending_emails[user_id] = verification
    google_client.send_email(email, str(verification.code),
                        'Texas A&M Cybersecurity Club' if guild_id == 631254092332662805 else 'TAMUctf')
    return "Please use /verify with the code you received in your email."


def verify_email(code: int, user_id: int):
    if user_id in pending_emails:
        pend_email = pending_emails[user_id]
        if pend_email.code == code:
            c.execute(
                "UPDATE users SET email = ? WHERE user_id = ?",
                (pend_email.email, user_id),
            )
            conn.commit()
            pending_emails.pop(user_id)
            return "Email verified! It is now visible on your /profile"
        else:
            return "This code is not correct!"
    else:
        return "Please use /register to submit your email"


def remove_pending(user_id: int = 0):
    del pending_emails[user_id]


def profile(user_id: int):
    c.execute(
        "SELECT name, points, attended, grad_year, email FROM users WHERE user_id = ?",
        (user_id,),
    )
    query = c.fetchone()
    if query is None:
        return "Your profile does not exist", None
    return "", query


def find_event(code: str = "", name: str = ""):
    if name == "" and code == "":
        return "Please include an event name or code.", None
    elif code == "":
        c.execute(
            "SELECT name, points, date, code, resources, attended_users FROM events WHERE name = ?", (name,)
        )
    elif name == "":
        c.execute(
            "SELECT name, points, date, code, resources, attended_users FROM events WHERE code = ?", (code,)
        )
    else:
        c.execute(
            "SELECT name, points, date, code, resources, attended_users FROM events where name = ? AND code = ?",
            (name, code),
        )
    data = c.fetchone()
    if data is None:
        return "This event does not exist", None
    else:
        return "", data


def event_list():
    c.execute("SELECT name, date, code FROM events")
    return c.fetchall()[::-1]


def award(user_id: int, user_name: str, points: int):
    c.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
    name = c.fetchone()
    if name is None:
        return "This user has not registered yet!"
    else:
        name = name[0]
    c.execute(
        "UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id)
    )
    conn.commit()
    return f"Successfully added {points} points to {user_name} - {name}"

def calendar_events():
    return google_client.get_events()