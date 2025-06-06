# CyberHam

## Running the bot

### Prerequisite

```bash
git clone https://github.com/tamucybersec/CyberHam.git # the SSH link can used if that works
cd CyberHam
```

### Installation

```bash
# use python3.12 or greater
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Make sure you have a file called `config.toml` (stored at the root), as well as all auxiliary files in the `secrets` folder (stored in cyberham). They contain keys and credentials needed to run the backend.

### Execution

```bash
python -m cyberham
```

### On a Server

On a server, you need to make sure the instance persists until killed, not just until you log off of the session. To do so, use `screen`.

```bash
# apt install screen if it is not already installed
screen -S cyberham
# run the commands to run the backend
# detach from the screen with ctrl+a ctrl+d
```

Later, you can kill it using the following:

```bash
screen -r cyberham
exit
```

## Contributing

-   Coordinate with team to decide on tasks to do
-   Make a new branch named your feature
-   Make a PR once you are done
-   Someone else will review and merge your PR
