from utils.logger import get_logger
from utils.database import *
from typing import * 

from datetime import date, timedelta
import utils.postgres as postgres
import utils.database as database
import utils.api.akatsuki as akat
import utils.beatmaps as beatmaps
import utils.events as events
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
                res = session.get(database.DBTaskStatus, "akatsuki_score_lb")
                if not res or (time.time()-res.last_run)/60>15:
                    self.update_score_lb()
                    session.merge(database.DBTaskStatus(task_name="akatsuki_score_lb", last_run=time.time()), load=True)
                    session.commit()
                res = session.get(database.DBTaskStatus, "akatsuki_live_lb")
                if not res or (time.time()-res.last_run)/60>15:
                    self.update_live_lb()
                    session.merge(database.DBTaskStatus(task_name="akatsuki_live_lb", last_run=time.time()), load=True)
                    session.commit()
                res = session.get(database.DBTaskStatus, "akatsuki_clan_lb")
                if not res or (time.time()-res.last_run)/60>60:
                    self.update_clan_lb()
                    session.merge(database.DBTaskStatus(task_name="akatsuki_clan_lb", last_run=time.time()), load=True)
                    session.commit()
                res = session.get(database.DBTaskStatus, "akatsuki_check_banned")
                if not res or (time.time()-res.last_run)/60>120:
                    self.check_banned_users()
                    session.merge(database.DBTaskStatus(task_name="akatsuki_check_banned", last_run=time.time()), load=True)
                    session.commit()
            time.sleep(30)
    
    def process_queue(self):
        while True:
            with postgres.instance.managed_session() as session:
                queue = session.query(DBUserQueue).filter(datetime.datetime.now().date() > DBUserQueue.date).all()
                for user in queue:
                    logger.info(f"Processing user in queue: {user.user_id}")
                    user_info = akat.get_user_info(user_id=user.user_id)
                    if not user_info:
                        logger.error(f"Cannot update {user.user_id}! Investigating...")
                        if akat.ping_server():
                            logger.info(f"User {user.user_id} is banned.")
                            self.ban_user(session, user.user_id)
                            session.delete(user)
                            session.commit()
                        continue
                    if not session.query(DBUserInfo).filter(DBUserInfo.server == "akatsuki", DBUserInfo.user_id == user.user_id, DBUserInfo.mode == user.mode, DBUserInfo.relax == user.relax).first():
                        logger.info(f"Fetching {user.user_id} plays")
                        scores = akat.get_user_best(user.user_id, user.mode, user.relax, pages=100000)
                        most_played = akat.get_user_most_played(user.user_id, user.mode, user.relax, pages=10000)
                        if (playtime := session.get(DBAKatsukiPlaytime, (user.user_id, user.mode, user.relax))) is None:
                            playtime = DBAKatsukiPlaytime(user_id = user.user_id, mode = user.mode, relax = user.relax, submitted_plays = 0, unsubmitted_plays = 0, most_played = 0)
                        for played_map in most_played:
                            if (beatmap := beatmaps.load_beatmap(session, played_map['beatmap']['beatmap_id'])) is not None:
                                playtime.most_played += ((beatmap.length/beatmap.max_combo)*30) * played_map['playcount']
                        for score in scores:
                            if (beatmap := beatmaps.load_beatmap(session, score['beatmap']['beatmap_id'])) is not None:
                                divisor = 1.5 if score['mods'] & 64 else 1
                                playtime.submitted_plays += (beatmap.length)/divisor
                                session.merge(score_to_db(score, user_id=user.user_id, mode=user.mode, relax=user.relax))
                        session.add(DBUserInfo(
                            server = "akatsuki",
                            user_id = user.user_id,
                            mode = user.mode,
                            relax = user.relax,
                            score_fetched = datetime.datetime.now().date()
                        ))
                        session.merge(playtime, load=True)
                    first_places = akat.get_user_first_places(user.user_id, user.mode, user.relax, pages=100000)
                    for score in first_places[1]:
                        if not beatmaps.load_beatmap(session, score['beatmap']['beatmap_id']):
                            continue
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
                    update_user(session, user.user_id, user.mode, user.relax, user.date, user_info, add_to_queue=False, fetch_recent=False)
                    session.delete(user)
                    session.commit()
            time.sleep(30)

    def update_live_lb(self) -> List[DBLiveUser]:
        
        start = time.time()
        logger.info("Tracking leaderboard started.")
        modes = ((0,0),(0,1),(0,2),(1,0),(1,1),(2,0),(2,1),(3,0))
        
        
        with postgres.instance.managed_session() as session:

            for link in session.query(DBDiscordLink).all():
                if link.default_server != "akatsuki":
                    continue
                session.merge(DBUserQueue(
                    server = "akatsuki",
                    user_id = link.servers[link.default_server],
                    mode = link.default_mode,
                    relax = link.default_relax,
                    date = date.today()
                ))
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
                    session.merge(dbuser)
            session.commit()
            logger.info(f"Leaderboard update took {(time.time()-start)/60:.2f} minutes. (Users to update: {len(to_update)})")
            self.update_users(to_update)
    
    def update_users(self, users: List[DBLiveUser]):
        
        start = time.time()
        logger.info("Updating users started.")
        
        by_id: Dict[int, List[DBLiveUser]] = {}
        for user in users:
            if user.user_id not in by_id:
                by_id[user.user_id] = []
            by_id[user.user_id].append(user)
        with postgres.instance.managed_session() as session:
            date = datetime.datetime.now().date()
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
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
                    update_user(session, user_id, user.mode, user.relax, date, user_info)
            inactive_updated = 0
            for user in session.query(DBStats).filter(DBStats.server == "akatsuki", DBStats.date == date).all():
                if user.user_id in by_id:
                    continue
                inactive_updated += 1
                if (pp := session.get(DBLiveUser, ("akatsuki", user.user_id, user.mode, user.relax))) is not None:
                    user.global_rank = pp.global_rank
                    user.country_rank = pp.country_rank
                if (score := session.get(DBLiveUserScore, ("akatsuki", user.user_id, user.mode, user.relax))) is not None:
                    user.global_score_rank = score.global_rank
                    user.country_score_rank = score.country_rank
                session.merge(user)
            for user in session.query(DBStats).filter(DBStats.server == "akatsuki", DBStats.date == yesterday).all():
                if not session.get(DBStats, (user.user_id, "akatsuki", user.mode, user.relax, date)):
                    inactive_updated += 1
                    stats = DBStats(
                        user_id = user.user_id,
                        server = "akatsuki",
                        mode = user.mode,
                        relax = user.relax,
                        date = date,
                        ranked_score = user.ranked_score,
                        total_score = user.total_score,
                        play_count = user.play_count,
                        play_time = user.play_time,
                        replays_watched = user.replays_watched,
                        total_hits = user.total_hits,
                        level = user.level,
                        accuracy = user.accuracy,
                        pp = user.pp,
                        global_rank = -1,
                        country_rank = -1,
                        global_score_rank = -1,
                        country_score_rank = -1,
                        max_combo = user.max_combo,
                        first_places = user.first_places,
                        clears = user.clears,
                        xh_count = user.xh_count,
                        x_count = user.x_count,
                        sh_count = user.sh_count,
                        s_count = user.s_count,
                        a_count = user.a_count,
                        b_count = user.b_count,
                        c_count = user.c_count,
                        d_count = user.d_count
                    )
                    if (pp := session.get(DBLiveUser, ("akatsuki", stats.user_id, stats.mode, stats.relax))) is not None:
                        stats.global_rank = pp.global_rank
                        stats.country_rank = pp.country_rank
                    if (score := session.get(DBLiveUserScore, ("akatsuki", stats.user_id, stats.mode, stats.relax))) is not None:
                        stats.global_score_rank = score.global_rank
                        stats.country_score_rank = score.country_rank
                    session.add(stats)
            session.commit()
            logger.info(f"Users update took {(time.time()-start)/60:.2f} minutes. (active: {len(users)}, inactive: {inactive_updated})")

    def update_score_lb(self):
        modes = ((0,0),(0,1),(0,2),(1,0),(1,1),(2,0),(2,1),(3,0))
        start = time.time()
        logger.info("updating score leaderboard...")
        with postgres.instance.managed_session() as session:
            
            for user in session.query(DBLiveUserScore).filter(DBLiveUserScore.server == "akatsuki").all():
                session.delete(user)
                
            for mode, relax in modes:
                leaderboard = akat.get_leaderboard(mode=mode, relax=relax, pages=4, sort=akat.SortOption.SCORE)
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

                    dbuser = DBLiveUserScore(
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

                    session.merge(dbuser)

                session.commit()
            logger.info(f"Score leaderboard update took {(time.time()-start)/60:.2f} minutes.")

    def update_clan_lb(self):
        modes = ((0,0),(0,1),(0,2),(1,0),(1,1),(2,0),(2,1),(3,0))
        start = time.time()
        logger.info("updating clan leaderboards...")
        with postgres.instance.managed_session() as session:
            for mode, relax in modes:
                clans_first_places = {}
                apiclans = akat.get_clan_first_leaderboard(mode=mode, relax=relax, pages=10)
                apiclans_pp = akat.get_clan_leaderboard(mode=mode, relax=relax, pages=10)
                position = 0
                for clan, first_places in apiclans:
                    position += 1
                    if clan['clan'] not in clans_first_places:
                        clans_first_places[clan['clan']] = {'tag': clan['tag'], 'first_places': first_places, 'rank': position}
                for apiclan, stats in apiclans_pp:
                    if (clan := session.get(DBClan, ("akatsuki", apiclan['id']))) is None:
                        clan = DBClan(server="akatsuki", clan_id=apiclan['id'], name=apiclan['name'])
                    if apiclan['id'] in clans_first_places:
                        clan.tag = clans_first_places[apiclan['id']]['tag']
                    session.merge(DBClanStats(
                        server = "akatsuki",
                        clan_id = apiclan['id'],
                        mode = mode,
                        relax = relax,
                        date = datetime.datetime.now().date(),
                        global_rank = stats['global_leaderboard_rank'],
                        global_rank_1s = clans_first_places[apiclan['id']]['rank'] if apiclan['id'] in clans_first_places else -1,
                        first_places = clans_first_places[apiclan['id']]['first_places'] if apiclan['id'] in clans_first_places else -1,
                        ranked_score = stats['ranked_score'],
                        total_score = stats['total_score'],
                        play_count = stats['playcount'],
                        accuracy = stats['accuracy'],
                        pp = stats['pp'],
                    ))
                    session.merge(clan)
                session.commit()
        logger.info(f"clan leaderboard update took {(time.time()-start)/60:.2f} minutes.")

    def check_banned_users(self):
        with postgres.instance.managed_session() as session:
            for user in session.query(DBUser).filter(DBUser.server == "akatsuki", (datetime.datetime.now() - DBUser.latest_activity) < timedelta(days=59)).all():
                if session.query(DBLiveUser).filter(DBLiveUser.server == "akatsuki", DBLiveUser.user_id == user.user_id).count() == 0:
                    if akat.ping_server() and not akat.get_user_info(user.user_id):
                        logger.info(f"found banned user {user.username} ({user.user_id})")
                        self.ban_user(session, user.user_id)

    def ban_user(self, session: postgres.Session, user_id: int):
        for link in session.query(DBDiscordLink).all():
            if 'akatsuki' in link.servers:
                if link.servers['akatsuki'] == user_id:
                    events.queue.submit("user_banned", user_id=user_id, server="akatsuki", linked=True)
                    return # Ignore linked users, mostly autoban
        events.queue.submit("user_banned", user_id=user_id, server="akatsuki", linked=False)
        logger.info(f"Wiping {user_id}")
        for first_place in session.query(DBUserFirstPlace).filter(
                DBUserFirstPlace.server == "akatsuki",
                DBUserFirstPlace.user_id == user_id
        ).all():
            session.delete(first_place)
        for info in session.query(DBUserInfo).filter(
                DBUserInfo.server == "akatsuki",
                DBUserInfo.user_id == user_id
        ).all():
            session.delete(info)
        for playtime in session.query(DBAKatsukiPlaytime).filter(
                DBAKatsukiPlaytime.user_id == user_id
        ).all():
            session.delete(playtime)
        for stats in session.query(DBStats).filter(
                DBStats.server == "akatsuki",
                DBStats.user_id == user_id
        ).all():
            session.delete(stats)
        for user in session.query(DBUser).filter(
                DBUser.server == "akatsuki",
                DBUser.user_id == user_id
        ).all():
            session.delete(user)
        for score in session.query(DBScore).filter(
                DBScore.server == "akatsuki",
                DBScore.user_id == user_id
        ).all():
            session.delete(score)
        session.commit()

def update_user(session, user_id: int, mode: int, relax: int, date: date, user_info: akat.User, add_to_queue=True, fetch_recent=True):
    stats = session.query(DBStats).filter(DBStats.server == "akatsuki", DBStats.user_id == user_id, DBStats.mode == mode, DBStats.relax == relax, DBStats.date == date).first()
    queue = True
    if stats:
        queue = False
        session.delete(stats)
    first_places_count = akat.get_user_first_places(user_id=user_id, mode=mode, relax=relax)[0]
    stats = stats_to_db(session, user_id, mode, relax, date, first_places_count, user_info)
    if (score_user := session.get(DBLiveUserScore, ("akatsuki", user_id, mode, relax))) is not None:
        stats.global_score_rank = score_user.global_rank
        stats.country_score_rank = score_user.country_rank
    session.merge(stats)
    if add_to_queue:
        if queue:
            session.merge(DBUserQueue(
                server = "akatsuki",
                user_id = user_id,
                mode = mode,
                relax = relax,
                date = (date - datetime.timedelta(days=1)),
            ))
        session.merge(DBUserQueue(
            server = "akatsuki",
            user_id = user_id,
            mode = mode,
            relax = relax,
            date = date,
    ))
    if not fetch_recent:
        return
    if (playtime := session.get(DBAKatsukiPlaytime, (user_id, mode, relax))) is None:
        playtime = DBAKatsukiPlaytime(user_id = user_id, mode = mode, relax = relax, submitted_plays = 0, unsubmitted_plays = 0, most_played = 0)
    offset = 0
    while offset != -1:
        scores = akat.get_user_recent(user_id=user_id, mode=mode, relax=relax, pages=1, offset=offset)
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
            session.merge(score_to_db(score, user_id, mode, relax), load=True)
            session.commit()
        scores = {}
        for score in session.query(DBScore).filter(DBScore.server == "akatsuki", DBScore.completed == 3, DBScore.user_id == user_id).all():
            mode_str = f'{score.mode}+{score.relax}'
            if score.beatmap_id in scores:
                if mode_str in scores[score.beatmap_id]:
                    if score.date > scores[score.beatmap_id][mode_str].date:
                        scores[score.beatmap_id][mode_str].completed = 2
                        scores[score.beatmap_id][mode_str] = score
                    else:
                        scores[score.beatmap_id][mode_str] = score
                else:
                    scores[score.beatmap_id] = {mode_str: score}
        session.commit()
    session.merge(playtime, load=True)


def stats_to_db(session: postgres.Session, user_id: int, mode: int, relax: int, date: date, first_places_count: int, user_info: akat.User):
    modes = ['std', 'taiko', 'ctb', 'mania']
    mode_str = modes[mode]
    play_time = user_info['stats'][relax][mode_str]['playtime']
    if relax > 0:
        if (calculated_playtime := session.get(DBAKatsukiPlaytime, (user_id, mode, relax))) is not None:
            play_time = int(calculated_playtime.submitted_plays + calculated_playtime.unsubmitted_plays + calculated_playtime.most_played)
    return DBStats(
        server = "akatsuki",
        user_id = user_id,
        mode = mode,
        relax = relax,
        date = date,
        ranked_score = user_info['stats'][relax][mode_str]["ranked_score"],
        total_score = user_info['stats'][relax][mode_str]["total_score"],
        play_count = user_info['stats'][relax][mode_str]["playcount"],
        play_time = play_time,
        replays_watched = user_info['stats'][relax][mode_str]['replays_watched'],
        total_hits = user_info['stats'][relax][mode_str]['total_hits'],
        level = user_info['stats'][relax][mode_str]['level'],
        accuracy = user_info['stats'][relax][mode_str]['accuracy'],
        pp = user_info['stats'][relax][mode_str]['pp'],
        global_rank = user_info['stats'][relax][mode_str]['global_leaderboard_rank'],
        country_rank = user_info['stats'][relax][mode_str]['country_leaderboard_rank'],
        max_combo = user_info['stats'][relax][mode_str]['max_combo'],
        clears = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3).count(),
        xh_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "SSH"
            ).count() +
        session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "SSHD"
            ).count(),
        x_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "SS"
            ).count(),
        s_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "S"
            ).count(),
        sh_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "SH"
            ).count() + 
        session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "SHD"
            ).count(),
        a_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "A"
            ).count(),
        b_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "B"
            ).count(),
        c_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "C"
            ).count(),
        d_count = session.query(DBScore).filter(
            DBScore.user_id == user_id, 
            DBScore.mode == mode, 
            DBScore.relax == relax, 
            DBScore.completed == 3,
            DBScore.rank == "D"
            ).count(),
        
        first_places = first_places_count
    )

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