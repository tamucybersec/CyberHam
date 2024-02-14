# CyberHam

## Setting up the bot
### Creating the bot
Go to the [discord developer portal](https://discord.com/developers/applications/) and create a new application. Using the button on the top right.
![Create a bot profile](https://file.garden/ZcqcCFK3bnacTMc-/Application_Creation.png)
Go to the bot tab and reset the token. This is what you will put in the `discord_token` parameter in the config.toml file.
![Acquire the token to run the bot](https://file.garden/ZcqcCFK3bnacTMc-/Token_Reset.png)
On the same page, turn off public bot and set the Priviledge Gateway Intents as shown below.
![Declaring the intents of the bot](https://file.garden/ZcqcCFK3bnacTMc-/Bot_Intents.png)
### Inviting the bot
Copy your application id on the General Information tab, and put this into this url
![Acquiring application/bot ID](https://file.garden/ZcqcCFK3bnacTMc-/Application_Id.png)
Then insert the application id into this url, replacing "{APPLICATIONID}" with your number.
`https://discord.com/api/oauth2/authorize?client_id={APPLICATIONID}&permissions=3072&scope=bot%20applications.commands`
This is the discord bot invite link,(giving it only read/write message perms). You use to add the bot to your testing server.
### Getting the guild id
The guild/server id can be located in the widget tab in the server settings.
![Acquiring Guild ID](https://file.garden/ZcqcCFK3bnacTMc-/Guild_Id.png)
This is the guild id you include into the `test_guild_ids` parameter in the config.toml

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
