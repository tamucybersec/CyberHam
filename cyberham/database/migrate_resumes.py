import os
from cyberham.database.typeddb import usersdb, resumesdb, db
from cyberham.types import Resume
from cyberham.database.backup import write_backup
from datetime import datetime, timezone

def migrate_resumes():
    # get all users
    all_users = usersdb.get_all()
    write_backup("users", all_users)
    print("Backed up old table")

    # create resumes db table (same as what sqlite.py would do, but this is intended to run before everything else)
    db.cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resumes (
            user_id TEXT PRIMARY KEY, 
            filename TEXT NOT NULL,
            format TEXT NOT NULL,
            upload_date TEXT NOT NULL, --stored when the file gets written to disk
            is_valid INTEGER NOT NULL CHECK(is_valid IN (0, 1)), --has it been verified by an officer? (adding that next)
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE
        )"""
    )
    db.conn.commit()

    if not os.path.exists("resumes"):
        print("No resumes directory found????????")
        return
    has_errors: list[str] = []
    for user_id in os.listdir("resumes"): # files get written to the user_id of their uploader
        # try getting filename and format from user first (works for uploads after resume indicator update)
        # if they aren't there, then they just weren't stored at all and will be empty strings until it's updated
        user = usersdb.get((user_id,))
        if user is None:
            print(f"Warning: resume file for unknown user {user_id}")
            has_errors.append(user_id)
            continue
    
        filename = user["resume_filename"] # type: ignore 
        format = user["resume_format"] # type: ignore
        
        # get last modified time for that file (so, when it was written to disk during its upload)
        resume_path = os.path.join("resumes", user_id)
        upload_date = datetime.fromtimestamp(os.path.getmtime(resume_path), tz=timezone.utc).isoformat().replace("+00:00", "Z")
        
        # skip resumes that already got entered into the resumes table (if this isn't the first time running this)
        existing_resume = resumesdb.get((user_id,))
        if existing_resume is not None:
            print(f"Resume for user {user_id} already migrated. skipping")
            continue

        # then create a resume entry with that user's id, filename, format, the time we got, and is_valid = 0
        resume_entry = Resume(
            user_id = user["user_id"],
            filename = filename, # type: ignore
            format = format, # type: ignore
            upload_date = upload_date,
            is_valid = 0 # for resume verification later on
        ) 
        # insert that entry into the resumes table
        resumesdb.create(resume_entry)
        print(f"Migrated resume for user {user["user_id"]}")

    # remove old columns from users table
    if len(has_errors) == 0: # so it doesn't delete the possibly existing data for those resumes until that's dealt with
        db.cursor.execute("ALTER TABLE users DROP COLUMN resume_filename;")
        db.cursor.execute("ALTER TABLE users DROP COLUMN resume_format;")
        db.conn.commit()
        print("Resume info migrated to db table successfully!")
    else:
        print("Files not migrated (no matching user in usersdb):\n")
        for id in has_errors:
            print(id)
    

if __name__ == "__main__":
    migrate_resumes()