from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import asyncio
import json
import gzip
import time


class DataFile:
    def __init__(self, filepath) -> None:
        # Create parent directory
        Path([item[::-1] for item in filepath[::-1].split("/", 1)][::-1][0]).mkdir(
            parents=True, exist_ok=True
        )
        self.filepath: str = filepath
        self.data: Optional[dict] = None

    def load_data(self, default={}):
        self.wait_lock()
        self.lock()
        try:
            with gzip.open(self.filepath, "r") as fin:
                self.data = json.loads(fin.read().decode("utf-8"))
        except:
            self.data = default
        self.unlock()

    def save_data(self):
        self.wait_lock()
        if not self.data:
            self.load_data()
        self.lock()
        with gzip.open(self.filepath, "w") as fout:
            fout.write(json.dumps(self.data).encode("utf-8"))
        self.unlock()

    def delete(self):
        Path(self.filepath).unlink(missing_ok=True)

    def wait_lock(self):
        elapsed = 0.0
        while Path(f"{self.filepath}.lock").exists():
            time.sleep(0.1)
            elapsed += 0.1
            if elapsed > 30:  # Most likely a dead lock
                self.unlock()

    def lock(self):
        Path(f"{self.filepath}.lock").touch(exist_ok=True)

    def unlock(self):
        Path(f"{self.filepath}.lock").unlink(missing_ok=True)

    def exists(self):
        return exists(self.filepath)

    async def wait_till_exist(self, timeout=60):
        time = datetime.now()
        while True:
            if exists(self.filepath):
                return True
            if (datetime.now() - time) > timedelta(seconds=timeout):
                return False
            await asyncio.sleep(delay=1)


class BinaryFile(DataFile):
    def load_data(self):
        self.wait_lock()
        self.lock()
        try:
            with gzip.open(self.filepath, "r") as fin:
                self.data = fin.read()
        except:
            self.data = None
        self.unlock()

    def save_data(self):
        self.wait_lock()
        if not self.data:
            self.load_data()
        self.lock()
        with gzip.open(self.filepath, "w") as fout:
            fout.write(self.data)
        self.unlock()


def exists(filepath):
    return Path(filepath).exists()
