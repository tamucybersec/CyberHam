# CyberHam

## Running the bot
### Installation
```bash
python -m venv venv
pip install -r requirements.txt
source venv/bin/activate
```
### Configuration
in config.toml, set the following values:
- google_client: the file name of the client_secret.json file you downloaded from google cloud API and is placed in cyberham/secrets/
- discord_token: the discord token for the bot
- test_guild_ids: a list of guild ids for the bot to sync commands to

### Execution
```bash
python -m cyberham
```

## Contributing
- Coordinate with team to decide on tasks to do
- make a new branch named your feature
- make a PR once you are done
- someone else will review and merge your PR