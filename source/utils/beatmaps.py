from akatsuki_pp_py import Beatmap as calc_beatmap
from akatsuki_pp_py import Calculator

from utils.files import BinaryFile, exists
from utils.logger import get_logger

from database import DBBeatmap
from ossapi import Beatmap
import utils.mods as mods

import api.akatsuki
import datetime
import requests
import config

DEFAULT_HEADERS = {"user-agent": "akatsukialt!/KompirBot fetch service"}
logger = get_logger("beatmaps")

def download_beatmap(beatmap_id, force_download=False) -> bool:
    if exists(f"{config.BASE_PATH}/beatmaps/{beatmap_id}.osu.gz" and not force_download):
        return True
    if result := _osudirect_download(beatmap_id):
        return result

    # Use old.ppy.sh as backup endpoint
    return _ppy_download(beatmap_id)


def _osudirect_download(beatmap_id) -> bool:
    response = requests.get(
        f"https://osu.direct/api/osu/{beatmap_id}",
        headers=DEFAULT_HEADERS,
    )
    if not response.ok:
        logger.warning(f"GET {response.url} {response.status_code}")
        logger.warning(f"{response.text}")
        return False
    logger.info(f"GET {response.url} {response.status_code}")
    file = BinaryFile(f"{config.BASE_PATH}/beatmaps/{beatmap_id}.osu.gz")
    file.data = response.content
    file.save_data()
    return True


def _ppy_download(beatmap_id) -> bool:
    response = requests.get(
        f"https://old.ppy.sh/osu/{beatmap_id}",
        headers=DEFAULT_HEADERS,
    )
    if not response.ok or not response.content:
        logger.warning(f"GET {response.url} {response.status_code}")
        logger.warning(f"{response.text}")
        return False
    logger.info(f"GET {response.url} {response.status_code}")
    file = BinaryFile(f"{config.BASE_PATH}/beatmaps/{beatmap_id}.osu.gz")
    file.data = response.content
    file.save_data()
    return True

def get_calc_beatmap(beatmap_id):
    path = f"{config.BASE_PATH}/beatmaps/{beatmap_id}.osu.gz"
    if not exists(path):
        if not download_beatmap(beatmap_id):
            logger.warn(f"Map {beatmap_id} can't be downloaded!")
            return
    file = BinaryFile(path)
    file.load_data()
    return calc_beatmap(bytes=file.data)

def get_star_rating(calc_beatmap: calc_beatmap):
    stars = list()
    mods_combo = [0, mods.Easy, mods.HardRock, mods.DoubleTime, mods.DoubleTime+mods.Easy, mods.DoubleTime+mods.HardRock]
    for mod in mods_combo:
        calc = Calculator(mods=mod)
        max_perf = calc.performance(calc_beatmap)
        stars.append(max_perf.difficulty.stars)
    return stars

def beatmap_to_db(beatmap: Beatmap):
    downloaded = download_beatmap(beatmap.id)
    stars_nm = stars_ez = stars_hr = stars_dt = stars_dtez = stars_dthr = 0
    if downloaded:
        try:
            stars_nm, stars_ez, stars_hr, stars_dt, stars_dtez, stars_dthr = get_star_rating(get_calc_beatmap(beatmap.id))
        except:
            logger.warn(f"Can't calculate star rating for map {beatmap.id}", exc_info=True)
    akat_beatmap = api.akatsuki.get_map_info(beatmap.id)
    approved_date = 0
    if beatmap._beatmapset.ranked_date:
        approved_date = beatmap._beatmapset.ranked_date.timestamp()
    elif beatmap.last_updated:
        approved_date = beatmap.last_updated.timestamp()
    return DBBeatmap(
        beatmap_id=beatmap.id, 
        beatmap_set_id=beatmap.beatmapset_id, 
        beatmap_md5=beatmap.checksum,
        artist=beatmap._beatmapset.artist,
        title=beatmap._beatmapset.title,
        version=beatmap.version,
        mapper=beatmap._beatmapset.creator,
        ranked_status={'bancho': beatmap.status.value, 'akatsuki': akat_beatmap["ranked"]-1},
        last_checked=datetime.datetime.now(),
        ar=beatmap.ar,
        od=beatmap.accuracy,
        cs=beatmap.cs,
        length=beatmap.hit_length,
        bpm=beatmap.bpm,
        max_combo=beatmap.max_combo,
        circles=beatmap.count_circles,
        sliders=beatmap.count_sliders,
        spinners=beatmap.count_spinners,
        mode=beatmap.mode.value,
        tags=beatmap._beatmapset.tags,
        packs=",".join(beatmap._beatmapset.pack_tags) if beatmap._beatmapset.pack_tags else "",
        approved_date = approved_date,
        stars_nm=stars_nm,
        stars_ez = stars_ez,
        stars_hr = stars_hr,
        stars_dt = stars_dt,
        stars_dtez = stars_dtez,
        stars_dthr = stars_dthr
    )
    