from utils.logger import get_logger
from utils.database import *
from typing import * 

import utils.postgres as postgres
import utils.database as database
import utils.api.akatsuki as akat
import time

logger = get_logger("akatsuki_tracker")

class AkatsukiTracker():
    
    def __init__(self) -> None:
        pass
    
    def main(self):
        while True:    
            with postgres.instance.managed_session() as session:
                res = session.get(database.DBTaskStatus, "akatsuki_live_lb")
                if not res or (time.time()-res.last_run)/60>15:
                    self.update_live_lb()
                    session.merge(database.DBTaskStatus(task_name="akatsuki_live_lb", last_run=time.time()), load=True)
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
                dbuser = session.query(DBUser).filter(DBUser.server == "akatsuki", DBUser.user_id == user_id).first()
                dbuser.latest_activity = user_info['latest_activity']
                dbuser.country = user_info['country']
                dbuser.clan = user_info["clan"]['id']
                dbuser.followers = user_info['followers']
                # TODO: add clan to database
                
                for user in by_id[user_id]:
                    date = datetime.now().date()
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
            session.commit()
            logger.info(f"Users update took {(time.time()-start)/60:.2f} minutes.")
