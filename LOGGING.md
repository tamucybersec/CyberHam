# CyberHam Logging System

## Overview

CyberHam now includes a comprehensive logging system that tracks security-relevant events throughout the application. All security events are logged to a dedicated `security.log` file with timestamps and detailed context.

## What is Logged

### 1. Authentication Attempts
- **Location**: Dashboard `/login` endpoint and all API endpoints requiring authentication
- **Information logged**:
  - Token used (first 8 characters for privacy)
  - Permission level of the token
  - Success or failure status
  - Endpoint being accessed
  - Timestamp

**Example log entries:**
```
2024-02-05 15:30:45 - INFO - [AUTH SUCCESS] Token: abc12345..., Permission: ADMIN, Time: 2024-02-05T15:30:45.123456, Endpoint: /login
2024-02-05 15:31:12 - WARNING - [AUTH FAILED] Token: invalid1..., Permission: NONE, Time: 2024-02-05T15:31:12.654321
```

### 2. Elevated Privilege Operations
- **Location**: Discord bot admin commands
- **Operations logged**:
  - `award_points` - Manual point awards to users
  - `delete_all_events` - Deletion of all Discord events
  - `update_calendar_events` - Importing events from Google Calendar
- **Information logged**:
  - Operation name
  - Discord user ID performing the operation
  - Discord user name
  - Additional details about the operation
  - Timestamp

**Example log entries:**
```
2024-02-05 15:32:10 - WARNING - [ELEVATED] Operation: delete_all_events, Time: 2024-02-05T15:32:10.123456, User ID: 123456789, User Name: AdminUser, Details: Deleting 5 Discord events
2024-02-05 15:33:00 - WARNING - [ELEVATED] Operation: award_points, Time: 2024-02-05T15:33:00.654321, User ID: 987654321, User Name: CommitteeMember, Details: Awarded 100 points to JohnDoe (ID: 111222333)
```

### 3. CRUD Operations
- **Location**: Dashboard API endpoints (users, events, attendance, points, tokens, flagged)
- **Operations logged**: CREATE, UPDATE, DELETE, REPLACE
- **Information logged**:
  - Operation type
  - Table/resource being modified
  - Token used (first 8 characters for privacy)
  - Permission level
  - Record ID being modified
  - Additional details
  - Timestamp

**Example log entries:**
```
2024-02-05 15:34:20 - INFO - [CRUD CREATE] Table: users, Token: xyz98765..., Permission: ADMIN, Time: 2024-02-05T15:34:20.123456, Record ID: user_123
2024-02-05 15:35:15 - WARNING - [CRUD DELETE] Table: events, Token: def54321..., Permission: SUPER_ADMIN, Time: 2024-02-05T15:35:15.654321, Record ID: event_456
2024-02-05 15:36:00 - INFO - [CRUD REPLACE] Table: attendance, Token: ghi11111..., Permission: ADMIN, Time: 2024-02-05T15:36:00.123456, Details: Replacing with 42 records
```

## Log Files

### security.log
- **Purpose**: Security audit trail
- **Mode**: Append (preserves history)
- **Level**: INFO and above
- **Format**: `YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE`
- **Location**: Root directory of the project

### Other Log Files
- `discord.log` - Discord library debug logs
- `cyberham.log` - General application logs
- `bot.log` - Bot-specific logs

## Log Levels

- **INFO**: Normal security events (successful authentication, non-deletion CRUD operations)
- **WARNING**: Security-sensitive operations (failed authentication, elevated privilege operations, deletion operations)

## Privacy Considerations

To protect sensitive information:
- **Tokens**: Only the first 8 characters are logged, followed by "..."
- **Full tokens are NEVER logged** to prevent unauthorized access if logs are compromised
- **User IDs and names**: Logged for accountability of privileged operations

## Monitoring Recommendations

### Regular Reviews
1. Review `security.log` regularly for unusual patterns:
   - Multiple failed authentication attempts from the same or different tokens
   - Unexpected elevated privilege operations
   - Unusual deletion patterns
   - Access outside normal hours

### Alerts to Configure
Consider setting up alerts for:
- Multiple authentication failures in a short time period
- Deletion of critical records (events, users, tokens)
- Use of SUPER_ADMIN privileges
- Operations from unexpected user IDs

### Log Rotation
The `security.log` file is in append mode to preserve history. Consider implementing log rotation:
```bash
# Example logrotate configuration
/path/to/security.log {
    weekly
    rotate 52
    compress
    delaycompress
    missingok
    notifempty
}
```

## Accessing Logs

### View Recent Security Events
```bash
tail -f security.log
```

### Search for Failed Authentication Attempts
```bash
grep "AUTH FAILED" security.log
```

### Find All DELETE Operations
```bash
grep "CRUD DELETE" security.log
```

### Check Elevated Operations by Specific User
```bash
grep "User ID: 123456789" security.log
```

### View Logs from Specific Date
```bash
grep "2024-02-05" security.log
```

## Implementation Details

The logging system is implemented in `cyberham/utils/logger.py` and provides four main functions:
- `log_auth_attempt()` - For authentication events
- `log_elevated_operation()` - For privileged bot commands
- `log_crud_operation()` - For database modifications via API
- `log_dashboard_access()` - For dashboard endpoint access

These are called automatically throughout the application where security-relevant operations occur.
