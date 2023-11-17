from datetime import datetime, timedelta
from utils.beatmaps import load_beatmap

from utils.logger import get_logger
from threading import Thread
from utils.database import *
from typing import *

import utils.api.titanic as titanic
import utils.postgres as postgres
import time

logger = get_logger("titanic_tracker")

class TitanicTracker():
    
    def __init__(self) -> None:
        pass
    
    def main(self):
        queue_thread = Thread(target=self.process_queue)
        queue_thread.start()
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
    
    def process_queue(self):
        while True:
            with postgres.instance.managed_session() as session:
                queue = session.query(DBUserQueue).filter(DBUserQueue.server == "titanic", datetime.now().date() > DBUserQueue.date).all()
                for user in queue:
                    logger.info(f"Processing user in queue: {user.user_id}")
                    if not session.query(DBUserInfo).filter(DBUserInfo.server=="titanic", DBUserInfo.mode == user.mode, DBUserInfo.user_id == user.user_id).first():
                        clears: List[titanic.Score] = list()
                        page = 1
                        while True:
                            res = titanic.get_user_top(user_id=user.user_id, mode=user.mode, page=page)
                            if not res:
                                break
                            clears.extend(res)
                            page += 1
                        for clear in clears:
                            if (beatmap := load_beatmap(session, clear['beatmap']['id'])) is not None:
                                session.merge(self.score_to_db(clear))
                    session.commit()
                    first_places: List[titanic.Score] = list()
                    page = 1
                    while True:
                        res = titanic.get_user_first_places(user_id=user.user_id, mode=user.mode, page=page)
                        if not res:
                            break
                        first_places.extend(res)
                        page += 1
                    for first_place in first_places:
                        if (beatmap := load_beatmap(session, first_place['beatmap']['id'])) is not None:
                            session.merge(self.score_to_db(first_place))
                            session.merge(DBUserFirstPlace(
                                server = "titanic",
                                user_id = user.user_id,
                                mode = user.mode,
                                relax = 0,
                                date = user.date,
                                score_id = f"titanic.{first_place['id']}"
                            ))
                    session.merge(DBUserInfo(
                        server = "titanic",
                        user_id = user.user_id,
                        mode = user.mode,
                        relax = user.relax,
                        score_fetched = datetime.today()
                    ), load=True)
                    session.delete(user)
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
                            country_rank = user['score_rank_country'], 
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
        old_users = [{}, {}, {}, {}]
        new_users = {}
        with postgres.instance.managed_session() as session:
            for user in session.query(DBLiveUser).filter(DBLiveUser.server == "titanic").all():
                old_users[user.mode][user.user_id] = user.play_count
                session.delete(user)
            for mode in modes:
                page = 1
                while True:
                    if not (users := titanic.get_user_lb(mode, titanic.LeaderboardType.pp, page=page)):
                        break
                    for user in users: 
                        new_users[user['user_id']] = user['user']['name']
                        session.add(DBLiveUser(
                            server = "titanic",
                            user_id = user["user_id"],
                            mode = mode,
                            relax = 0,
                            global_rank = user['index'],
                            country_rank = user['country_rank'], # TODO
                            ranked_score = user['user']['stats'][mode]['rscore'],
                            total_score = user['user']['stats'][mode]['tscore'],
                            play_count = user['user']['stats'][mode]['playcount'],
                            replays_watched = user['user']['stats'][mode]['replay_views'],
                            total_hits = user['user']['stats'][mode]['total_hits'],
                            level = 0, # TODO
                            accuracy = user['user']['stats'][mode]['acc']*100,
                            pp = user['user']['stats'][mode]['pp']
                        ))
                        
                        if user['user_id'] not in old_users[mode] or user['user']['stats'][mode]['playcount'] > old_users[mode][user['user_id']]:
                            if not session.query(DBUserQueue).filter(DBUserQueue.server=="titanic", DBUserQueue.user_id == user['user_id'], DBUserQueue.mode == mode).first():
                                if not session.query(DBUserInfo).filter(DBUserInfo.mode == mode, DBUserInfo.server == "titanic", DBUserInfo.user_id == user['user_id']).first():
                                    date = datetime.today().date()-timedelta(days=1)
                                else:
                                    date = datetime.today().date()
                                session.add(DBUserQueue(server="titanic", user_id=user['user_id'], mode=mode, relax=0, date=date))
                
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

    def score_to_db(self, score: titanic.Score) -> DBScore:
        return DBScore(
            beatmap_id = score['beatmap']['id'],
            server = "titanic",
            user_id = score['user_id'],
            mode = score['mode'],
            relax = 0,
            score_id = f"titanic.{score['id']}",
            accuracy = score['acc']*100,
            mods = score['mods'],
            pp = score['pp'],
            score = score['total_score'],
            combo = score['max_combo'],
            rank = score['grade'],
            count_300 = score['n300'],
            count_100 = score['n100'],
            count_50 = score['n50'],
            count_miss = score['nMiss'],
            completed = 3,
            date = int(datetime.strptime(score['submitted_at'], titanic.date_format).timestamp())
        )