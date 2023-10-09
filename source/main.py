from threading import Thread

from tasks.beatmaps import BeatmapMaintainer
from tasks.statistics import StatisticsTracker
from tasks.akatsuki import AkatsukiTracker

import signal
import time
import sys

suspended = False

def signal_handler(sig, frame):
    global suspended
    suspended = True

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    threads = [
        Thread(target=BeatmapMaintainer().main),
        Thread(target=StatisticsTracker().main),
        Thread(target=AkatsukiTracker().main),
    ]
    
    for thread in threads:
        thread.start()

    # Wait threads
    for thread in threads:
        thread.join()

    # Exit    
    sys.exit(0)