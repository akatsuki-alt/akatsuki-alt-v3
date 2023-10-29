from utils.database import DBMetricsRequests
import utils.postgres as postgres
import requests
import time

class RequestHandler:
    
    def __init__(self, req_min=60, headers={'user-agent': 'akatsuki_alt_project'}) -> None:
        self.delay = 60/req_min
        self.headers = headers
        self.last_call = 0

    def get(self, url: str):
        elapsed = time.time() - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay-elapsed)
        self.last_call = time.time()
        start = time.time()
        req = requests.get(url, headers=self.headers)
        end = (time.time() - start)*1000
        with postgres.instance.managed_session() as session:
            if (metrics := session.get(DBMetricsRequests, url.split("?")[0])) is None:
                metrics = DBMetricsRequests(url=url.split("?")[0], requests=0, avg_response_time=end)
                session.add(metrics)
            metrics.requests += 1
            metrics.avg_response_time = (metrics.avg_response_time+end)/2
            session.commit()
        return req