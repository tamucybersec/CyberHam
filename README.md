# CyberHam

## Running the bot
### Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### Configuration
Create a config.toml file in the root of the repo and set the following values:
```toml
google_client = "client_secret_2_{FILL IN -> client_id}.apps.googleusercontent.com.json" # the file name of the client_secret.json file you downloaded from google cloud API and is placed in cyberham/secrets/
discord_token = "" # the discord token for the bot as a str
test_guild_ids = [] # [631254092332662805] is the cyber club server, the id of discord guilds in a comma seperated int array
```

### Execution
```bash
python -m cyberham
```

## Contributing
- Coordinate with team to decide on tasks to do
- make a new branch named your feature
- make a PR once you are done
- someone else will review and merge your PR
