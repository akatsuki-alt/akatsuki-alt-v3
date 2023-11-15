from threading import Thread

from tasks.beatmaps import BeatmapMaintainer
from tasks.akatsuki import AkatsukiTracker
from tasks.titanic import TitanicTracker

import discordbot.bot
import utils.events
import gamebot.bot
import api.main
import signal
import time
import sys

suspended = False

def signal_handler(sig, frame):
    global suspended
    suspended = True

def event_listener():
    events = utils.events.queue.listen()
    for func, args, kwargs in events: 
        func(*args, **kwargs)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    threads = [
        Thread(target=event_listener),
        Thread(target=BeatmapMaintainer().main),
        Thread(target=AkatsukiTracker().main),
        Thread(target=api.main.main),
        Thread(target=discordbot.bot.main),
        Thread(target=gamebot.bot.main),
        Thread(target=TitanicTracker().main)
    ]
    
    for thread in threads:
        thread.start()

    # Wait threads
    for thread in threads:
        thread.join()

    # Exit    
    sys.exit(0)