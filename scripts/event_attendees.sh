#!/bin/sh
sqlite3 ./cyberham/db/attendance.db <<EOF
SELECT name, attended_users FROM events;
EOF
