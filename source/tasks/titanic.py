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
            time.sleep(5)
    
    def update_score_lb(self):
        start = time.time()
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
            logger.info(f"Updating score leaderboard took {time.time()-start:.0f} seconds")
    
    def update_live_lb(self):
        start = time.time()
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
                        
                        if (dbuser := session.get(DBUser, (user['user_id'], 'titanic'))) is None:
                            dbuser = DBUser()
                            session.add(dbuser)
                            
                        dbuser.user_id = user['user_id']
                        dbuser.server = "titanic"
                        dbuser.username = user['user']['name']
                        dbuser.registered_on = datetime.strptime(user['user']['created_at'], titanic.date_format)
                        dbuser.latest_activity = datetime.strptime(user['user']['latest_activity'], titanic.date_format)
                        dbuser.country = user['user']['country']
                        dbuser.clan = 0
                        dbuser.followers = -1
                        
                        if (stats := session.get(DBStats, (user['user_id'], "titanic", mode, 0, datetime.today().date()))) is None:
                            stats = DBStats()
                            session.add(stats)
                            
                        stats.user_id = user['user_id']
                        stats.server = "titanic"
                        stats.mode = mode
                        stats.relax = 0
                        stats.date = datetime.today()
                        stats.ranked_score = user['user']['stats'][mode]['rscore']
                        stats.total_score = user['user']['stats'][mode]['tscore']
                        stats.play_count = user['user']['stats'][mode]['playcount']
                        stats.play_time = user['user']['stats'][mode]['playtime']
                        stats.replays_watched = user['user']['stats'][mode]['replay_views']
                        stats.total_hits = user['user']['stats'][mode]['total_hits']
                        stats.level = 0, # TODO
                        stats.accuracy = user['user']['stats'][mode]['acc']*100
                        stats.pp = user['user']['stats'][mode]['pp']
                        stats.global_rank = user['global_rank']
                        stats.country_rank = user['country_rank']
                        stats.global_score_rank = user['score_rank']
                        stats.country_score_rank = user['score_rank_country']
                        stats.max_combo = user['user']['stats'][mode]['max_combo']
                        stats.first_places = -1
                        stats.clears = sum([v if '_count' in k else 0 for k,v in user['user']['stats'][mode].items()])
                        stats.xh_count = user['user']['stats'][mode]['xh_count']
                        stats.x_count = user['user']['stats'][mode]['x_count']
                        stats.sh_count = user['user']['stats'][mode]['sh_count']
                        stats.s_count = user['user']['stats'][mode]['s_count']
                        stats.a_count = user['user']['stats'][mode]['a_count']
                        stats.b_count = user['user']['stats'][mode]['b_count']
                        stats.c_count = user['user']['stats'][mode]['c_count']
                        stats.d_count = user['user']['stats'][mode]['d_count']
                    page+=1

            session.commit()
            logger.info(f"Updating live leaderboard took {time.time()-start:.0f} seconds")
