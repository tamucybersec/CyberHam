# __main__.py is the entry point of the app
# used to start all the services (discord bot and api server)

from threading import Thread
from multiprocessing import Process
from cyberham.bot.bot import run_bot
from cyberham.apis.dashboard import run_api
from cyberham.database.backup import write_full_backup
import signal
import sys
import time
from types import FrameType


def periodic_backup():
    while True:
        time.sleep(60 * 60 * 24)  # 24 hours
        print("Running full backup...")
        try:
            write_full_backup()
            print("Backup complete. Sleeping for 24 hours...")
        except Exception as e:
            print(f"Backup failed: {e}")


def main():
    bot_process = Process(target=run_bot)
    api_process = Process(target=run_api)
    backup_thread = Thread(target=periodic_backup, daemon=True)

    # Start both processes and thead
    bot_process.start()
    api_process.start()
    backup_thread.start()

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
