from ossapi import BeatmapsetSearchCategory
from utils.logger import get_logger
import utils.postgres as postgres
import utils.database as database
import utils.api.bancho as bancho
import utils.beatmaps as beatmaps
import utils.selfbot as selfbot
from sqlalchemy import or_, Integer

from datetime import datetime, timedelta
from typing import *
import time
import re

logger = get_logger("beatmap_maintainer")

class BeatmapMaintainer():
    
    def __init__(self) -> None:
        pass
    
    def main(self):
        while True:    
            with postgres.instance.managed_session() as session:
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
            time.sleep(30)
    
    def update_bancho_maps(self):
        logger.info("Fetching bancho beatmaps...")
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
                                logger.info(f"Adding {beatmap.id}")
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
    
    def update_akatsuki_maps(self, full_run=False):
        logger.info("Fetching akatsuki beatmaps...")
        MARKDOWN_URL_REGEX = r"\[(.*?)\]\((\S*)(?:\s'(.*?)')?\)"
        found: List[selfbot.Message] = list()
        for x in range(0, 10000000 if full_run else 250 ,25):
            logger.info(f"crawling {x}...")
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
                logger.info(f"updating {id}")
                try:
                    beatmap = bancho.client.beatmap(beatmap_id=id)
                    time.sleep(0.5)
                except:
                    logger.info(f"can't update {id}, not found.")
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