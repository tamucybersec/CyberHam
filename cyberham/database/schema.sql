CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    grad_semester TEXT NOT NULL,
    grad_year INTEGER NOT NULL,
    major TEXT NOT NULL,
    email TEXT NOT NULL,
    verified INTEGER NOT NULL CHECK(verified IN (0, 1)),
    sponsor_email_opt_out INTEGER NOT NULL DEFAULT 0 CHECK(sponsor_email_opt_out IN (0, 1)),
    join_date TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resumes (
    user_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    format TEXT NOT NULL,
    upload_date TEXT NOT NULL,
    is_valid INTEGER NOT NULL CHECK(is_valid IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    points INTEGER NOT NULL,
    date TEXT NOT NULL,
    semester TEXT NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS flagged (
    user_id TEXT PRIMARY KEY,
    offenses INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance (
    user_id TEXT NOT NULL,
    code TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE,
    FOREIGN KEY (code) REFERENCES events(code) ON UPDATE CASCADE,
    PRIMARY KEY (user_id, code)
);

CREATE TABLE IF NOT EXISTS points (
    user_id TEXT,
    points INTEGER NOT NULL,
    semester TEXT NOT NULL,
    year INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE,
    PRIMARY KEY (user_id, semester, year)
);

CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created TEXT NOT NULL,
    expires_after TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    revoked INTEGER NOT NULL CHECK(revoked IN (0, 1)),
    permission INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS register (
    ticket TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verify (
    user_id TEXT PRIMARY KEY,
    code INTEGER
);

CREATE TABLE IF NOT EXISTS rsvp (
    user_id TEXT NOT NULL,
    code TEXT NOT NULL,
    reservation INTEGER NOT NULL CHECK (reservation IN (0, 1, 2)),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE,
    FOREIGN KEY (code) REFERENCES events(code) ON UPDATE CASCADE,
    PRIMARY KEY (user_id, code)
);
