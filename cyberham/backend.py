import random
import string

from typing import Literal
from datetime import datetime

from cyberham.config import conn, c
from cyberham.cyberclub_email import CyberClub, EmailPending

pending_emails = {}
out_mail = CyberClub()


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
    conn.commit()


def create_event(name: str, points: int, date: str, resources: str):
    code = ""
    code_list = [0]
    while code_list is not None:
        code = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
        c.execute("SELECT name FROM events WHERE code = ?", (code,))
        code_list = c.fetchone()  # returns tuple of one if exists otherwise none

    c.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, '')",
        (name, code, points, date, resources),
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
    if str(user_id) in attended_users.split():
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
        "UPDATE events SET attended_users = attended_users || ?",
        (f" {user_id}",),
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


def register(name: str, grad_year: int, email: str, user_id: int, user_name: str):
    c.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?, 0, 0, 0, '')",
        (user_id, user_name),
    )
    conn.commit()
    if not 1950 < grad_year < 2030:
        return "Please set your graduation year in the format of 202X"

    email = email.lower()
    if (
        "," in email
        or ";" in email
        or email.count("@") != 1
        or not email.endswith("tamu.edu")
    ):
        return "Please set a proper TAMU email address"

    c.execute("SELECT email FROM users WHERE user_id = ?", (user_id,))
    temp = c.fetchone()
    if temp is not None and temp[0] == email:
        ask_to_verify = ""
    else:
        verification = EmailPending(
            user_id, email, random.randint(1000, 10000), datetime.now()
        )
        pending_emails[user_id] = verification
        out_mail.send_email(email, str(verification.code))
        ask_to_verify = "Please use /verify with the code you received in your email"

    c.execute(
        "UPDATE users SET name = ?, grad_year = ? WHERE user_id = ?",
        (name, grad_year, user_id),
    )
    conn.commit()
    return f"You have successfully updated your profile! {ask_to_verify}"


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


def profile(user_id: int):
    c.execute(
        "SELECT name, points, attended, grad_year, email FROM users WHERE user_id = ?",
        (user_id,),
    )
    return c.fetchone()


def find_event(code: str = "", name: str = ""):
    if name == "" and code == "":
        return "Please include an event name or code.", None
    elif code == "":
        c.execute(
            "SELECT name, points, date, resources FROM events WHERE name = ?", (name,)
        )
    elif name == "":
        c.execute(
            "SELECT name, points, date, resources FROM events WHERE code = ?", (code,)
        )
    else:
        c.execute(
            "SELECT name, points, date, resources FROM events where name = ? AND code = ?",
            (name, code),
        )
    data = c.fetchone()
    if data is None:
        return "This event does not exist", None
    else:
        return "", data


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
