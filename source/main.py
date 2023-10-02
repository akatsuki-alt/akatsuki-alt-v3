from threading import Thread

from tasks.beatmaps import BeatmapMaintainer
from tasks.statistics import StatisticsTracker

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
    ]
    
    for thread in threads:
        thread.start()
    
    # Waits for termination signal
    while not suspended:
        time.sleep(1)
    
    # Wait threads
    for thread in threads:
        thread.join()
    
    sys.exit(0)