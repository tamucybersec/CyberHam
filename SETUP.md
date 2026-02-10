# Discord Bot

## Setting up the bot

### Creating the bot

Go to the [discord developer portal](https://discord.com/developers/applications/) and create a new application. Using the button on the top right.

<img alt="Create a bot profile" src="https://file.garden/ZcqcCFK3bnacTMc-/Application_Creation.png" width="50%"/>

Go to the bot tab and reset the token. This is what you will put in the `[discord]` `token` field in your `config.local.toml` file.

<img alt="Reset the bot token" src="https://file.garden/ZcqcCFK3bnacTMc-/Token_Reset.png" width="70%"/>

On the same page, turn off public bot and set the Priviledge Gateway Intents as shown below.

<img alt="Declare bot intents" src="https://file.garden/ZcqcCFK3bnacTMc-/Bot_Intents.png" width="70%"/>

### Inviting the bot

Copy your application id on the General Information tab, and put this into this url

<img alt="Aquire the client ID of your bot" src="https://file.garden/ZcqcCFK3bnacTMc-/Application_Id.png" width="70%"/>

Then insert the application id into this url, replacing "{APPLICATIONID}" with your number.
`https://discord.com/api/oauth2/authorize?client_id={APPLICATIONID}&permissions=3072&scope=bot%20applications.commands`
This is the discord bot invite link,(giving it only read/write message perms). You use to add the bot to your testing server.

### Getting the guild id

The guild/server id can be located in the widget tab in the server settings.

<img alt="Acquire a test guild ID" src="https://file.garden/ZcqcCFK3bnacTMc-/Guild_Id.png" width="70%"/>

This is the guild id you include into the `test_guild_ids` field in your `config.local.toml`

# Port Forwarding

Since the api runs on localhost in the cyber range, we need to forward the port to reach outside targets. We accomplish this using nginx

# Server

- Set an A name DNS record for api.cybr.club to the ip address on cloudflare
    - Set to run as proxy through cloudflare (so we use their certs)
    - Set SSL/TLS mode to full so it only operates over https 
- Run nginx, with config files found at /etc/nginx/sites-available and /etc/nginx/sites-enabled 
    - The one under sites-enabled is a symlink to sites-available
    - Has the following contents

```
server {
    listen 443 ssl;
    server_name api.cybr.club;
    include snippets/snakeoil.conf;

    location / {
        proxy_pass http://127.0.0.1:PORT/;
    }
}
```

- The server is a VM on the cyber range named "Nginx/Website/API"
- Just run the bot in terminal, no need to set up screens and such