# CyberHam

CyberHam is a collection of two important services used by the Texas A&M Cybersecurity Club: a bot which connects to discord and an api used by the dashboard. They are run as separate processes and communicate with one centralized local database to accomplish their purposes.

# Initial Setup

## Download the Code

- Clone the code from the repository

```bash
git clone https://github.com/tamucybersec/CyberHam
cd CyberHam
```

## Setup the Environment

- We use [uv](https://docs.astral.sh/uv/) to manage python, the virtual environment, and dependencies
- The project requires exactly python3.12
    - We use specific features of python3.12 in the project, but discord.py stopped support at python3.12
    - You don't need to install it yourself; uv will download python3.12 automatically if it isn't already on your system

### Install uv

- Follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/), or:

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Unix / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Dependencies

- From the root of the project, run:

```bash
uv sync
```

## Download Secrets

- Get an invite to the Tech Committee Discord Server
- Create a `secrets` folder at the root of your project (same level as this README.md)
- Everything the app needs that isn't in git lives in this folder

### Config Files

- Download all `.toml` files from the `#secrets` channel (you'll need the `@member` role first)
- Place them in the `secrets` folder
- These handle all the environment variables for the app
- The config is split across two files, which are merged together at startup:
    - `config.toml` is the base config shared by every environment
    - `config.<environment>.toml` holds the environment-specific values
        - Any value here overrides the same value in `config.toml`
- For the `config.dev.toml` file, follow the [setup guide for the discord bot](SETUP.md#discord-bot)

### Google Files

- Download and place the `client_secret..json` file from the `#secrets` channel in the `secrets` folder

## Running the Application


```bash
uv run python -m cyberham
```

### Troubleshooting

- In case you run into any errors during this step, there are a few actions you can take
- The most likely issue is that the virtual environment is set up incorrectly
    - For vscode: `ctrl+shift+p` > Python: Select Interpreter > Python3.12 ('.venv': venv)
    - If you get any further errors: delete your `.venv` folder and run `uv sync` again

## Authentication

- After running, you'll be prompted to log into a gmail account
    - In prod, it's running under the club's account, but during development you'll be using your own account
- You'll be warned **Google hasn’t verified this app**
    - Click `Go to CyberHam (unsafe)` because you trust the developer
- Next, you'll be prompted that **CyberHam wants additional access to your Google Account**
    - See below for precisely what permissions are used, then click `continue` because you trust CyberHam
- You should see a `token.json` file in your `secrets` folder if you successfully authenticate

### What are these permissions used for?

- The permissions are used in two parts of the app
    - Email verification during registration where we send an email to people that register
    - Event generation where we automatically generate the week's events in discord from google calendar

## Testing

- Once you have the app successfully running, here's what you'll have accomplished
    - You'll have an api open on your localhost, usefully for testing and developing the website `cybr.club`
    - You'll be connected to the discord bot on the Tech Committee discord server for testing (permitted nobody else is already connected)
- You'll need an invite to the Tech Committee server to now test if it's fully working
    - Go to the `#test-admin-channel` and type any command
    - If successful, you should see no errors and an update in your local database

## Managing the Database

### SQLite Tools

- Install `sqlite3` to manage your local database

### Windows

- Download the CLI tools from the official site: [sqlite.org](https://sqlite.org/download.html)
- Extract the `.zip` and add the folder to your system PATH (recommended), or just put the executable in the root of this project

### Unix / WSL

- `sqlite3` usually can be installed via your package manager

### sqlite

- To access the database:

```bash
sqlite3 cyberham.db
```

> The database will be automatically created once you run the project

- Once in the cli, you can run SQL commands directly:

```sql
.tables;
-- or any other sql commands, obviously
```

## Developer Settings

- Below are some required settings you'll need when developing to ensure you're aligning with proper type safety (as python doesn't naturally come with these safeties)
- Add the following your `settings.json` in vscode (`ctrl+shift+p` > Preferences: Open User Settings (JSON))

```jsonc
"python.analysis.diagnosticMode": "workspace",
"python.analysis.typeCheckingMode": "strict",
"python.analysis.diagnosticSeverityOverrides": {
    "reportUnknownMemberType": "information"
},
"python.analysis.inlayHints.functionReturnTypes": true, // optional, but helpful
"python.analysis.inlayHints.variableTypes": true, // optional, but helpful
```
