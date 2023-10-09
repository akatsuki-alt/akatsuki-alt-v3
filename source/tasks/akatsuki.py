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
    
    def update_live_lb(self):
        
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