# __main__.py is the entry point of the app
# used to start all the services (discord bot and api server)

from threading import Thread
from cyberham.bot.bot import run_bot
from cyberham.apis.dashboard import run_api


def run_threads():
    # run_api()
    Thread(target=run_api, daemon=True).start()
    run_bot()  # run one process on the main thread so the program doesn't quit


run_threads()
