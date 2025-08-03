# CyberHam

CyberHam is a collection of two important services used by the Texas A&M Cybersecurity Club: a bot which connects to discord and an api used by the dashboard. They are run as separate processes and communicate with one centralized local database to accomplish their purposes.

# Initial Setup

## Download the Code

-   Clone the code from the repository

```bash
git clone https://github.com/tamucybersec/CyberHam
cd CyberHam
```

## Setup the Environment

-   Regardless of your system, you'll need to install python3.12
    -   Use `python --version` to see your current python version
    -   We use specific features of python3.12 in the project, but discord.py stopped support at python3.12, so you need exactly python3.12 to develop this project

### Windows

-   Install the correct python version from [python.org](https://www.python.org/downloads/release/python-31210/)
    -   The last available version with an installer is 3.12.10
    -   Make sure you enable `also set environment variables` during the installation process or you'll either need to set the environment variable yourself or configure a python version manager

```bash
# requires python3.12

python -m venv venv
.\venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Unix / WSL

-   Use your package manager to install python3.12
    -   Run it specifically with `python3.12`, or set it as your default version through other means

```bash
# requires python3.12

python3 -m venv venv
# or python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Download Config Files

-   Log into [vw.cybr.club](https://vw.cybr.club)

### Config Files

-   Download all `.toml` files from the CyberHam entry in vault warden
-   Place them in the root of the project (same level as this README.md)
-   These handle all the environment variables for the app

### Secrets Files

-   Create a `secrets` folder at the root of your project (same level as this README.md)
-   Download and place the `client_secret..json` file there

## Running the Application

-   Make sure you're in the proper virtual environment (which was set by the `activate` script from the [Setup the Environment](#setup-the-environment) step)

### Windows

```bash
python -m cyberham
```

### Unix / WSL

```bash
python3 -m cyberham
# or python3.12 -m cyberham
```

### Troubleshooting

-   In case you run into any errors during this step, there are a few actions you can take
-   The most likely issue is that you set up the virtual environment incorrectly
    -   For vscode: `ctrl+shift+p` > Python: Select Interpreter > Python3.12 ('venv': venv)
    -   If you get any further errors: `exit` your virtual environment, delete your `venv` folder, and restart from [Setup the Environment](#setup-the-environment)

## Authentication

-   After running, you'll be prompted to log into a gmail account
    -   In prod, it's running under the club's account, but during development you'll be using your own account
-   You'll be warned **Google hasn’t verified this app**, you'll have to acknowledge this warning and click continue
-   You should see a `token.json` file in your `secrets` folder if you successfully authenticate
-   **Why do you need these permissions?**
    -   The permissions are used in two parts of the app
        -   Email verification during registration where we send an email to people that register
        -   Event generation where we automatically generate the week's events in discord from a google calendar

## Testing

-   Once you have the app successfully running, here's what you'll have accomplished
    -   You'll have an api open on your localhost, usefully for testing and developing the website `cybr.club`
    -   You'll be connected to the discord bot on the Tech Committee discord server for testing (permitted nobody else is already connected)
-   You'll need an invite to the Tech Committee server to now test if it's fully working
    -   Go to the `#test-admin-channel` and type any command
    -   If successful, you should see no errors and an update in your local database

## Managing the Database

-   Install `sqlite3` to manage your local database

### Windows

-   Download the CLI tools from the official site: [sqlite.org](https://sqlite.org/download.html)
-   Extract the `.zip` and add the folder to your system PATH (recommended), or just put the executable in the root of this project

### Unix / WSL

-   `sqlite3` usually can be installed via your package manager

### sqlite

-   To access the database:

```bash
sqlite3 cyberham.db
```

> The database will be automatically created once you run the project

-   Once in the cli, you can run SQL commands directly:

```sql
.tables;
-- or any other sql commands, obviously
```

## Developer Settings

-   Below are some required settings you'll need when developing to ensure you're aligning with proper type safety (as python doesn't naturally come with these safeties)
-   Add the following your `settings.json` in vscode (`ctrl+shift+p` > Preferences: Open User Settings (JSON))

```jsonc
"python.analysis.diagnosticMode": "workspace",
"python.analysis.typeCheckingMode": "strict",
"python.analysis.diagnosticSeverityOverrides": {
    "reportUnknownMemberType": "information"
},
"python.analysis.inlayHints.functionReturnTypes": true, // optional, but helpful
"python.analysis.inlayHints.variableTypes": true, // optional, but helpful
```

# Contributing

-   Coordinate with team to decide on tasks to do
-   Make a new branch named your feature
-   Make a PR once you are done
-   Someone else will review and merge your PR
