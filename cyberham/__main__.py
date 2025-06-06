# __main__.py is the entry point of the app
# used to start all the services (discord bot and api server)

from multiprocessing import Process
from cyberham.bot.bot import run_bot
from cyberham.apis.dashboard import run_api
import signal
import sys
from types import FrameType


def main():
    bot_process = Process(target=run_bot)
    api_process = Process(target=run_api)

    # Start both processes
    bot_process.start()
    api_process.start()

    # Define signal handler to stop both
    def shutdown(sig: int, frame: FrameType | None):
        print("\nShutting down...")
        bot_process.terminate()
        api_process.terminate()
        bot_process.join()
        api_process.join()
        sys.exit(0)

    # Attach signal handler
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Wait for both processes
    bot_process.join()
    api_process.join()
    sys.exit(0)


if __name__ == "__main__":
    main()
