from sqlalchemy.orm.attributes import flag_modified
from ossapi import BeatmapsetSearchCategory
from utils.api.servers import servers
from utils.logger import get_logger
from sqlalchemy import or_, Integer
import utils.postgres as postgres
import utils.database as database
import utils.api.bancho as bancho
import utils.beatmaps as beatmaps
import utils.selfbot as selfbot

from datetime import datetime, timedelta
from utils.database import *
from typing import *
import math
import time
import re

logger = get_logger("beatmap_maintainer")

class BeatmapMaintainer():
    
    def __init__(self) -> None:
        pass
    
    def main(self):
        while True:    
            with postgres.instance.managed_session() as session:
                #res = session.get(database.DBTaskStatus, "import_beatmaps")
                #if not res:
                #    self.import_beatmaps()
                #    session.merge(database.DBTaskStatus(task_name="import_beatmaps", last_run=time.time()), load=True)
                #    session.commit()
                res = session.get(database.DBTaskStatus, "bancho_beatmaps")
                if not res or (time.time()-res.last_run)/60/60>1:
                    self.update_bancho_maps()
                    session.merge(database.DBTaskStatus(task_name="bancho_beatmaps", last_run=time.time()), load=True)
                    session.commit()
                res = session.get(database.DBTaskStatus, "akatsuki_beatmaps")
                if not res or (time.time()-res.last_run)/60/60>1:
                    self.update_akatsuki_maps(full_run=not res)
                    session.merge(database.DBTaskStatus(task_name="akatsuki_beatmaps", last_run=time.time()), load=True)
                    session.commit()
                res = session.get(database.DBTaskStatus, "fix_beatmaps")
                if not res or (time.time()-res.last_run)/60/60>1:
                    self.fix_status()
                    session.merge(database.DBTaskStatus(task_name="fix_beatmaps", last_run=time.time()), load=True)
                    session.commit()
                res = session.get(database.DBTaskStatus, "build_beatmap_cache")
                if not res or (time.time()-res.last_run)/60/60>1:
                    self.build_beatmap_cache()
                    session.merge(database.DBTaskStatus(task_name="build_beatmap_cache", last_run=time.time()), load=True)
                    session.commit()
            time.sleep(30)
    
    def update_bancho_maps(self):
        logger.info("Fetching bancho beatmaps...")
        added = 0
        with postgres.instance.managed_session() as session:
            try:
                cursor = None
                found = False
                while True:
                    result = bancho.client.search_beatmapsets(category=BeatmapsetSearchCategory.HAS_LEADERBOARD, cursor=cursor)
                    cursor = result.cursor
                    if not result.beatmapsets:
                        break
                    for beatmapset in result.beatmapsets:
                        for beatmap in beatmapset.beatmaps:
                            if session.get(database.DBBeatmap, beatmap.id):
                                found = True
                                break
                            else:
                                added += 1
                                #logger.info(f"Adding {beatmap.id}")
                                beatmap._beatmapset = beatmapset
                                session.merge(beatmaps.beatmap_to_db(beatmap), load=True)
                        session.commit()
                        session.flush()
                        if found:
                            break
                    if found:
                        break
            except:
                pass
        logger.info(f"Added {added} bancho beatmaps.")

    def update_akatsuki_maps(self, full_run=False):
        logger.info("Fetching akatsuki beatmaps...")
        MARKDOWN_URL_REGEX = r"\[(.*?)\]\((\S*)(?:\s'(.*?)')?\)"
        found: List[selfbot.Message] = list()
        for x in range(0, 10000000 if full_run else 250 ,25):
            messages = selfbot.search_channel(offset=x)
            if not messages:
                logger.info('messages done.')
                break
            found.extend(messages)
        found.reverse()
        statuses = {'ranked': 0, 'loved': 4}
        maps = {}
        for message in found:
            message = message[0]
            if not message['embeds']:
                continue
            embed = message['embeds'][0]
            status = 0
            beatmap_id = int(re.match(MARKDOWN_URL_REGEX, embed['fields'][4]['value']).groups(1)[1].split("/")[-1])
            if embed['fields'][0]['value'].lower() in statuses:
                status = statuses[embed['fields'][0]['value'].lower()]
            maps[beatmap_id] = status
        logger.info(f"Found {len(maps)} Akatsuki updates")
        with postgres.instance.managed_session() as session:
            for id, _ in maps.items():
                #logger.info(f"updating {id}")
                try:
                    beatmap = bancho.client.beatmap(beatmap_id=id)
                    time.sleep(0.5)
                except:
                    if (beatmap := beatmaps.load_beatmap(session, id)) is not None:
                        beatmap.ranked_status['akatsuki'] = -2
                        flag_modified(beatmap, 'ranked_status')
                        session.commit()
                    continue
                session.merge(beatmaps.beatmap_to_db(beatmap), load=True)
                session.commit()
                session.flush()
    
    def fix_status(self):
        logger.info("Updating beatmaps status...")
        with postgres.instance.managed_session() as session:
            new_ranked = session.query(database.DBBeatmap).filter(
                (datetime.now() - database.DBBeatmap.last_checked) > timedelta(days=7),
                database.DBBeatmap.ranked_status['bancho'].astext.cast(Integer) > 0,
                or_(database.DBBeatmap.ranked_status['akatsuki'].astext.cast(Integer) == 3,
                database.DBBeatmap.ranked_status['akatsuki'].astext.cast(Integer) < 1),
            ).all()
            qualified = session.query(database.DBBeatmap).filter(
                (datetime.now() - database.DBBeatmap.last_checked) > timedelta(days=3),
                database.DBBeatmap.ranked_status['bancho'].astext.cast(Integer) == 3
            ).all()
            graveyard = session.query(database.DBBeatmap).filter(
                (datetime.now() - database.DBBeatmap.last_checked) > timedelta(days=21),
                database.DBBeatmap.ranked_status['bancho'].astext.cast(Integer) < 1
            ).all()
            to_check: Dict[int, database.DBBeatmap] = {}
            for beatmap in new_ranked:
                to_check[beatmap.beatmap_id] = beatmap
            for beatmap in qualified:
                to_check[beatmap.beatmap_id] = beatmap
            for beatmap in graveyard:
                to_check[beatmap.beatmap_id] = beatmap
            logger.info(f"Updating beatmap status (Akatsuki qualified: {len(new_ranked)}, Bancho qualified: {len(qualified)}, Graveyard: {len(graveyard)})")
            for id, beatmap in to_check.items():
                logger.info(f"updating {id}")
                try:
                    beatmap = bancho.client.beatmap(beatmap_id=id)
                    time.sleep(0.5)
                except:
                    logger.info(f"can't update {id}, not found.")
                    #session.delete(beatmap)
                    #session.commit()
                    #session.flush()
                    continue
                session.merge(beatmaps.beatmap_to_db(beatmap), load=True)
                session.commit()
                session.flush()

    def import_beatmaps(self):
        logger.info(f"Importing beatmaps...")
        imported = 0
        with postgres.instance.managed_session() as session:
            with open('/app/beatmaps.csv') as f:
                for line in f.readlines():
                    csv = line.split('\t')
                    if session.get(database.DBBeatmap, (int(csv[0]))):
                        continue
                    try:
                        session.merge(database.DBBeatmap(
                        beatmap_id = int(csv[0]),
                        beatmap_set_id = int(csv[1]),
                        beatmap_md5 = csv[2],
                        artist = csv[3],
                        title = csv[4],
                        version = csv[5],
                        mapper = csv[6],
                        ranked_status = {'bancho': int(csv[7]), 'akatsuki': int(csv[8])},
                        ar = float(csv[9]),
                        od = float(csv[10]),
                        cs = float(csv[11]),
                        length = int(csv[12].split('.')[0]),
                        bpm = float(csv[13]),
                        max_combo = int(csv[14]),
                        circles = int(csv[15]),
                        sliders = int(csv[16]),
                        spinners = int(csv[17]),
                        mode = int(csv[18]),
                        tags = csv[19],
                        packs = csv[20],
                        stars_nm = float(csv[21]),
                        stars_ez = float(csv[22]),
                        stars_hr = float(csv[23]),
                        stars_dt = float(csv[24]),
                        stars_dtez = float(csv[25]),
                        stars_dthr = float(csv[26]),
                        approved_date = int(csv[27].strip())
                    ))
                        imported += 1
                    except:
                        pass
            session.commit()
        logger.info(f"Imported {imported} maps.")
        
    def build_beatmap_cache(self):
        with postgres.instance.managed_session() as session:
            for object in session.query(database.DBCompletionCache):
                session.delete(object)
            processed = list()
            for server in servers:
                for set in server.beatmap_sets:
                    if set in processed:
                        continue
                    for x in range(12):
                        for mode in range(4):
                            cache = DBCompletionCache(key=f"stars_{set}_{mode}_{x}", value=0)
                            if x != 11:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.stars_nm >= x , DBBeatmap.stars_nm < x+1).count()
                            else:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.stars_nm >= x).count()
                            session.add(cache)
                    for x in range(12):
                        for mode in range(4):
                            cache = DBCompletionCache(key=f"od_{set}_{mode}_{x}", value=0)
                            if x != 11:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.od >= x , DBBeatmap.od < x+1).count()
                            else:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.od >= x).count()
                            session.add(cache)
                    for x in range(12):
                        for mode in range(4):
                            cache = DBCompletionCache(key=f"cs_{set}_{mode}_{x}", value=0)
                            if x != 11:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.cs >= x , DBBeatmap.cs < x+1).count()
                            else:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.cs >= x).count()
                            session.add(cache)
                    for x in range(12):
                        for mode in range(4):
                            cache = DBCompletionCache(key=f"ar_{set}_{mode}_{x}", value=0)
                            if x != 11:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.ar >= x , DBBeatmap.ar < x+1).count()
                            else:
                                cache.value = session.query(DBBeatmap).filter(DBBeatmap.ranked_status[set].astext.cast(Integer) > 0, DBBeatmap.mode == mode, DBBeatmap.ar >= x).count()
                            session.add(cache)
                                   
            session.commit()