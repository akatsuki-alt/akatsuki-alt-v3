from utils.logger import get_logger
from utils.database import *
from typing import * 

import utils.postgres as postgres
import utils.database as database
import utils.api.akatsuki as akat
import utils.beatmaps as beatmaps
from threading import Thread
import datetime 
import time

logger = get_logger("akatsuki_tracker")

class AkatsukiTracker():
    
    def __init__(self) -> None:
        pass
    
    def main(self):
        queue_thread = Thread(target=self.process_queue)
        queue_thread.start()
        while True:    
            with postgres.instance.managed_session() as session:
                res = session.get(database.DBTaskStatus, "akatsuki_live_lb")
                if not res or (time.time()-res.last_run)/60>15:
                    self.update_live_lb()
                    session.merge(database.DBTaskStatus(task_name="akatsuki_live_lb", last_run=time.time()), load=True)
                    session.commit()
            time.sleep(30)
    
    def process_queue(self):
        while True:
            with postgres.instance.managed_session() as session:
                queue = session.query(DBUserQueue).filter(datetime.datetime.now().date() > DBUserQueue.date).all()
                for user in queue:
                    logger.info(f"Processing user in queue: {user.user_id}")
                    if not session.query(DBUserInfo).filter(DBUserInfo.server == "akatsuki", DBUserInfo.mode == user.mode, DBUserInfo.relax == user.relax).first():
                        logger.info(f"Fetching {user.user_id} plays")
                        scores = akat.get_user_best(user.user_id, user.mode, user.relax, pages=100000)
                        most_played = akat.get_user_most_played(user.user_id, user.mode, user.relax, pages=10000)
                        if (playtime := session.get(DBAKatsukiPlaytime, (user.user_id, user.mode, user.relax))) is None:
                            playtime = DBAKatsukiPlaytime(user_id = user.user_id, mode = user.mode, relax = user.relax, submitted_plays = 0, unsubmitted_plays = 0, most_played = 0)
                        for map in most_played:
                            if (beatmap := beatmaps.load_beatmap(session, map['beatmap']['beatmap_id'])) is not None:
                                playtime.most_played += ((beatmap.length/beatmap.max_combo)*30) * map['playcount']
                        for score in scores:
                            if (beatmap := beatmaps.load_beatmap(session, map['beatmap']['beatmap_id'])) is not None:
                                divisor = 1.5 if score['mods'] & 64 else 1
                                playtime.submitted_plays += (beatmap.length)/divisor
                            session.add(score_to_db(score, user_id=user.user_id, mode=user.mode, relax=user.relax))
                        session.add(DBUserInfo(
                            server = "akatsuki",
                            user_id = user.user_id,
                            mode = user.mode,
                            relax = user.relax,
                            score_fetched = datetime.datetime.now().date()
                        ))
                        session.merge(playtime)
                    first_places = akat.get_user_first_places(user.user_id, user.mode, user.relax, pages=100000)
                    for score in first_places[1]:
                        if not session.query(DBScore).filter(DBScore.server == "akatsuki", DBScore.score_id == int(score['id'])).first():
                            session.add(score_to_db(score, user.user_id, user.mode, user.relax))
                        session.merge(DBUserFirstPlace(
                            server = "akatsuki",
                            user_id = user.user_id,
                            mode = user.mode,
                            relax = user.relax,
                            date = user.date,
                            score_id = int(score['id'])
                        ))
                    session.delete(user)
                    session.commit()
            time.sleep(30)

    def update_live_lb(self) -> List[DBLiveUser]:
        
        start = time.time()
        logger.info("Tracking leaderboard started.")
        modes = ((0,0),(0,1),(0,2),(1,0),(1,1),(2,0),(2,1),(3,0))
        
        with postgres.instance.managed_session() as session:

            old_users = session.query(DBLiveUser).filter(DBLiveUser.server == "akatsuki").all()
            to_update: List[DBLiveUser] = list()
            
            old_users_table = {}
            for mode, relax in modes:
                if mode not in old_users_table:
                    old_users_table[mode] = {}
                old_users_table[mode][relax] = {}

            for liveuser in old_users:
                old_users_table[liveuser.mode][liveuser.relax][liveuser.user_id] = liveuser            
                session.delete(liveuser)    
            
            for mode, relax in modes:
                leaderboard = akat.get_leaderboard(mode=mode, relax=relax, pages=50, sort=akat.SortOption.PP)
                for user, chosen_mode in leaderboard:
                    if not session.query(DBUser).filter(DBUser.server == "akatsuki", DBUser.user_id == user["id"]).first():
                        session.add(DBUser(
                            user_id = user['id'], 
                            server = "akatsuki",
                            username = user['username'],
                            registered_on = user['registered_on'],
                            latest_activity = user['latest_activity'],
                            country = user['country'],
                        ))
                    dbuser = DBLiveUser(
                        server="akatsuki",
                        user_id=user["id"],
                        mode=mode, 
                        relax=relax, 
                        global_rank=chosen_mode["global_leaderboard_rank"],
                        country_rank=chosen_mode["country_leaderboard_rank"],
                        ranked_score=chosen_mode["ranked_score"],
                        total_score=chosen_mode["total_score"],
                        play_count=chosen_mode["playcount"],
                        replays_watched=chosen_mode["replays_watched"],
                        total_hits=chosen_mode["total_hits"],
                        level=chosen_mode['level'],
                        accuracy=chosen_mode['accuracy'],
                        pp=chosen_mode['pp']
                    )
                    if old_users:
                        if dbuser.user_id in old_users_table[mode][relax]:
                            if dbuser.play_count > old_users_table[mode][relax][dbuser.user_id].play_count:
                                to_update.append(dbuser)
                        else:
                            to_update.append(dbuser)
                    session.add(dbuser)
            session.commit()
            logger.info(f"Leaderboard update took {(time.time()-start)/60:.2f} minutes. (Users to update: {len(to_update)})")
            self.update_users(to_update)
    
    def update_users(self, users: List[DBLiveUser]):
        
        start = time.time()
        logger.info("Updating users started.")
        
        by_id: Dict[int, List[DBLiveUser]] = {}
        modes = ['std', 'taiko', 'ctb', 'mania']
        for user in users:
            if user.user_id not in by_id:
                by_id[user.user_id] = []
            by_id[user.user_id].append(user)
        
        with postgres.instance.managed_session() as session:
            for user_id in by_id:
                user_info = akat.get_user_info(user_id)
                logger.info(f"Updating {user_info['username']}")
                dbuser = session.query(DBUser).filter(DBUser.server == "akatsuki", DBUser.user_id == user_id).first()
                dbuser.latest_activity = user_info['latest_activity']
                dbuser.country = user_info['country']
                dbuser.clan = user_info["clan"]['id']
                dbuser.followers = user_info['followers']
                session.merge(DBClan(
                    server = "akatsuki",
                    clan_id = user_info['clan']['id'],
                    name = user_info['clan']['name'],
                    tag = user_info['clan']['tag'],
                    description = user_info['clan']['description'],
                    icon = user_info['clan']['icon'],
                    owner = user_info['clan']['owner'],
                    status = user_info['clan']['status'],
                ))
                
                for user in by_id[user_id]:
                    date = datetime.datetime.now().date()
                    stats = session.query(DBStats).filter(DBStats.server == "akatsuki", DBStats.user_id == user_id, DBStats.mode == user.mode, DBStats.relax == user.relax, DBStats.date == date).first()
                    if stats:
                        session.delete(stats)
                    
                    first_places_count = akat.get_user_first_places(user_id=user_id, mode=user.mode, relax=user.relax)[0]
                    # TODO: Clear count, score rank
                    mode = modes[user.mode]
                    session.add(DBStats(
                        server = "akatsuki",
                        user_id = user_id,
                        mode = user.mode,
                        relax = user.relax,
                        date = date,
                        ranked_score = user_info['stats'][user.relax][mode]["ranked_score"],
                        total_score = user_info['stats'][user.relax][mode]["total_score"],
                        play_count = user_info['stats'][user.relax][mode]["playcount"],
                        play_time = user_info['stats'][user.relax][mode]['playtime'],
                        replays_watched = user_info['stats'][user.relax][mode]['replays_watched'],
                        total_hits = user_info['stats'][user.relax][mode]['total_hits'],
                        level = user_info['stats'][user.relax][mode]['level'],
                        accuracy = user_info['stats'][user.relax][mode]['accuracy'],
                        pp = user_info['stats'][user.relax][mode]['pp'],
                        global_rank = user_info['stats'][user.relax][mode]['global_leaderboard_rank'],
                        country_rank = user_info['stats'][user.relax][mode]['country_leaderboard_rank'],
                        max_combo = user_info['stats'][user.relax][mode]['max_combo'],
                        first_places = first_places_count
                    ))
                    session.merge(DBUserQueue(
                        server = "akatsuki",
                        user_id = user_id,
                        mode = user.mode,
                        relax = user.relax,
                        date = date,
                    ))
                    if (playtime := session.get(DBAKatsukiPlaytime, (user.user_id, user.mode, user.relax))) is None:
                        playtime = DBAKatsukiPlaytime(user_id = user.user_id, mode = user.mode, relax = user.relax, submitted_plays = 0, unsubmitted_plays = 0, most_played = 0)
                    offset = 0
                    while offset != -1:
                        scores = akat.get_user_recent(user_id=user_id, mode=user.mode, relax=user.relax, pages=1, offset=offset)
                        if not scores:
                            break
                        for score in scores:
                            if session.query(DBScore).filter(DBScore.server =="akatsuki", DBScore.score_id==int(score['id'])).first():
                                offset = -1
                                break
                            if (beatmap := beatmaps.load_beatmap(session, score['beatmap']['beatmap_id'])) is not None:
                                divisor = 1.5 if score['mods'] & 64 else 1
                                if score['completed'] > 1:
                                    playtime.submitted_plays += (beatmap.length)/divisor
                                else:
                                    playtime.unsubmitted_plays += ((beatmap.length/beatmap.max_combo) * (
                                        score['count_300'] + 
                                        score['count_100'] + 
                                        score['count_50']  +
                                        score['count_miss']
                                    )) / divisor
                            session.add(score_to_db(score, user_id, user.mode, user.relax))
            session.commit()
            logger.info(f"Users update took {(time.time()-start)/60:.2f} minutes.")

def score_to_db(score: akat.Score, user_id,  mode, relax):
    return DBScore(
            beatmap_id = score['beatmap']['beatmap_id'],
            server = "akatsuki",
            user_id = user_id,
            mode = mode,
            relax = relax,
            score_id = int(score['id']),
            accuracy = score['accuracy'],
            mods = score['mods'],
            pp = score['pp'],
            score = score['score'],
            combo = score['max_combo'],
            rank = score['rank'],
            count_300 = score['count_300'],
            count_100 = score['count_100'],
            count_50 = score['count_50'],
            count_miss = score['count_miss'],
            completed = score['completed'],
            date = datetime.datetime.fromisoformat(score["time"][:-1] + "+00:00").timestamp()
    )