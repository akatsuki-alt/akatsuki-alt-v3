import requests
import time

class RequestHandler:
    
    def __init__(self, req_min=60, headers={'user-agent': 'akatsuki_alt_project'}) -> None:
        self.delay = 60/req_min
        self.headers = headers
        self.last_call = 0

    def get(self, url):
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay-elapsed)
        self.last_call = time.time()
        return requests.get(url, headers=self.headers)
