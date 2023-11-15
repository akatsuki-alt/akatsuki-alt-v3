from utils.logger import get_logger
import utils.postgres as postgres
import utils.api.titanic as titanic
from utils.database import *
import time

logger = get_logger("titanic_tracker")

class TitanicTracker():
    
    def __init__(self) -> None:
        pass
    
    def main(self):
        while True:    
            with postgres.instance.managed_session() as session:
                res = session.get(DBTaskStatus, "titanic_score_lb")
                if not res or (time.time()-res.last_run)/60>15:
                    self.update_score_lb()
                    session.merge(DBTaskStatus(task_name="titanic_score_lb", last_run=time.time()), load=True)
                    session.commit()
                res = session.get(DBTaskStatus, "titanic_live_lb")
                if not res or (time.time()-res.last_run)/60>15:
                    self.update_live_lb()
                    session.merge(DBTaskStatus(task_name="titanic_live_lb", last_run=time.time()), load=True)
                    session.commit()
    
    def update_score_lb(self):
        logger.info("updating score leaderboard...")
        modes = (0,1,2,3)
        with postgres.instance.managed_session() as session:
            for user in session.query(DBLiveUserScore).filter(DBLiveUserScore.server == "titanic").all():
                session.delete(user)
            for mode in modes:
                page = 1
                while True:
                    if not (users := titanic.get_user_lb(mode, titanic.LeaderboardType.ranked_score, page=page)):
                        break
                    for user in users:
                        session.add(DBLiveUserScore(
                            server = "titanic",
                            user_id = user["user_id"],
                            mode = mode,
                            relax = 0,
                            global_rank = user['index'],
                            country_rank = 0, # TODO
                            ranked_score = user['user']['stats'][mode]['rscore'],
                            total_score = user['user']['stats'][mode]['tscore'],
                            play_count = user['user']['stats'][mode]['playcount'],
                            replays_watched = user['user']['stats'][mode]['replay_views'],
                            total_hits = user['user']['stats'][mode]['total_hits'],
                            level = 0, # TODO
                            accuracy = user['user']['stats'][mode]['acc']*100,
                            pp = user['user']['stats'][mode]['pp']
                        ))
                    page+=1
            session.commit()
    
    def update_live_lb(self):
        logger.info("updating live leaderboard...")
        modes = (0,1,2,3)
        with postgres.instance.managed_session() as session:
            for user in session.query(DBLiveUser).filter(DBLiveUser.server == "titanic").all():
                session.delete(user)
            for mode in modes:
                page = 1
                while True:
                    if not (users := titanic.get_user_lb(mode, titanic.LeaderboardType.pp, page=page)):
                        break
                    for user in users:
                        session.add(DBLiveUser(
                            server = "titanic",
                            user_id = user["user_id"],
                            mode = mode,
                            relax = 0,
                            global_rank = user['index'],
                            country_rank = 0, # TODO
                            ranked_score = user['user']['stats'][mode]['rscore'],
                            total_score = user['user']['stats'][mode]['tscore'],
                            play_count = user['user']['stats'][mode]['playcount'],
                            replays_watched = user['user']['stats'][mode]['replay_views'],
                            total_hits = user['user']['stats'][mode]['total_hits'],
                            level = 0, # TODO
                            accuracy = user['user']['stats'][mode]['acc']*100,
                            pp = user['user']['stats'][mode]['pp']
                        ))
                        session.merge(DBUser(
                            user_id = user['user_id'],
                            server = "titanic",
                            username = user['user']['name'],
                            registered_on = datetime.strptime(user['user']['created_at'], titanic.date_format),
                            latest_activity = datetime.strptime(user['user']['latest_activity'], titanic.date_format),
                            country = user['user']['country']
                            ))
                    page+=1
            session.commit()