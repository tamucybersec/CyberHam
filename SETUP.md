# Discord Bot

This setup guide will help you create the required resources to begin using the bot. This includes creating a google cloud account, a development server, the bot itself, and recording the required secrets.

To start off, create this `config.dev.toml` at the root of your project and paste the below inside. By the end, you should have this file completely filled out:

```toml
website_url = "http://localhost:3000"

[google]
client_file_name = ""

[discord]
token = ""
test_guild_ids = [0]
admin_channel_id = 0
```

> **Preface**: Discord updates very frequently so parts of this guide are likely outdated. If so, your best bet is probably finding a youtube video like "creating a discord bot 2026" and updating this guide to go along with that. Discord has really poor documentation so it'll probably be hard to find a static site that records all this information.

## Google Cloud

> This is recorded for documentation reasons. You should be able to grab the required config from the secrets channel of the server. Google Cloud Console requires a credit card to set up (even if they don't charge it for the free tier), so we won't require you to make an account for this.

In order to use a couple api for the project, we need to generate a config file from google cloud. Later, we will also have to log in to a google account through which the emails will be sent by.

### Setting up an account

- Go to https://console.cloud.google.com
    - Click the button "Create or select a project"
    - Click the button "New project"
    - Give it a descriptive name like "CyberHam Development"
    - Click "Create" and wait for it to be created
- Click "Select a project" in the top bar
    - Click the newly made project
    - In the top bar search "Gmail API" and enable it
    - Search "Google Calendar API" and enable it
- Go to "APIs and Services"
    - Click on "Credentials"
        - Click "Create credentials" then "OAuth Client ID"
    - Click "Configure Concent Screen"
        - Click "Get Started" and follow the prompts
    - Click "Create client"
        - Select application type "Web application"
        - Fill out a name
        - Click "Create"
        - Download the json from the popup
- Go to "Audience"
    - Publish the app

### Filling in the config

- Put the downloaded json into your secrets folder
    - Copy the name of the file and fill out the `google.client_file_name` field

## Setting up the server

For simplicity, you can create your own server to do development in. If you make your own server, you'll be the admin and be able to test any features you want for the bot. Just be careful with the required permission of the bot and permissions of those who use the command, as they need to be considered for security reasons (we don't want just anyone being able to use any command on the bot).

### Creating the server

- Open up Discord
    - Scroll to the bottom of your server list
    - Click the "+" icon
    - Click "Create my Own"
    - Click "For me and my friends"
    - Name it something descriptive like "CyberHam Development"
- Open the Server Settings page
    - On the roles tab
        - Create a role named "Admin"
            - Set the "Administrator" permission (should be at the very bottom)
            - Save your changes
        - Create a role named "Student"
            - Give it no permissions
            - Save your changes
- Create a new text channel
    - Call it "admins-only"
    - Make it a private channel
    - Give the "Admin" role access to the channel

> The purpose behind creating the roles is so you can view the bot through different lens. In the roles tab, clicking the three dots on a role will allow you to view the server as if you had those permissions. This will influence what commands you can make from the bot.

### Filling in the config

- Find the "admin-only" channel
    - Right click it and copy the link
        - The first number is the server id
            - Fill out the `discord.test_guild_ids` field in your config
                - It is a list of numbers, the only number being the server id you just found
        - The second number is the channel id
            - Fill out the `discord.admin_channel_id` field in your config
                - It is just one number, the only number being the channel id you just found

## Setting up the bot

### Creating the bot

- Go to https://discord.com/developers/applications
- Create new application using button "New Application"
    - Give it a descriptive name like "CyberHam-\<YourDiscordUsername\>"
- Go to the installation tab
    - In Installation Contexts, uncheck "user installation" (leaving only guild install)
    - In Install Link, set the option to "None"
- Go to the Bot tab
    - Set the Icon
        - Give it the same icon as your current discord profile icon, for simplicity
            - You can get this by using inspect element on the web version of discord
    - In the Authorization Flow section
        - Uncheck public bot
        - Check all intents (presence, server members, message content)
- Go to the OAuth2 tab
    - In OAuth2 URL Generator check 
        - bot
        - applications.commands
        - ...and probably a couple more we'll find out about
    - In Bot Permissions check 
        - Administrator
    - Copy the generated url at the bottom of the page, and paste it into your browser
        - Follow the prompts and invite it to the desired server

### Filling in the config

- Go to the Bot tab
    - Find token field
        - Click "Reset Token"
        - Copy the token and record it as the `discord.token` field in your config

# nginx

Since the api runs on localhost in the cyber range, we need to forward the port to reach outside targets. We accomplish this using nginx

## Server configs

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
