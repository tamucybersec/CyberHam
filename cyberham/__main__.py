from threading import Thread
from cyberham.discord_bot import run_bot
from cyberham.dashboard_api import run_api


def run_threads():
    # run_api()
    Thread(target=run_api, daemon=True).start()
    run_bot()

run_threads()
