from utils.api.request import RequestHandler
from enum import Enum
from typing import *

handler = RequestHandler(req_min=60)
modes = ['osu', 'taiko', 'fruits', 'mania']

class LeaderboardType(str, Enum):
    pp = "performance"
    ranked_score = "rscore"
    total_score = "tscore"
    country = "country"
    ppv1 = "ppv1"

class Achievement(TypedDict):
    category: str
    filename: str
    name: str
    unlocked_at: str
    user_id: int

class Relationship(TypedDict):
    status: int # 0: friend, other: blocked
    target_id: int # user friended
    user_id: int

class GameStats(TypedDict):
    acc: float # 1.00 for 100%
    max_combo: int
    total_hits: int
    playcount: int
    playtime: int
    rscore: int
    tscore: int
    mode: int
    pp: float
    ppv1: float
    rank: int
    replay_views: int
    xh_count: int
    x_count: int
    sh_count: int
    s_count: int
    a_count: int
    b_count: int
    c_count: int
    d_count: int

class Profile(TypedDict):
    
    achievements: List[Achievement]
    activated: bool
    badges: List
    country: str
    created_at: str
    id: int
    latest_activity: str
    name: str
    names: List[str]
    playstyle: int
    preferred_mode: int
    relationships: List[Relationship]
    restricted: bool
    silence_end: str
    stats: List[GameStats]

class Beatmapset(TypedDict):
    
    approved_at: str
    artist: str
    available: bool
    created_at: str
    creator: str
    genre_id: int
    has_storyboard: bool
    has_video: bool
    id: int
    language_id: int
    last_update: str
    osz_filesize: int
    osz_filesize_novideo: int
    server: int # 0: uploaded on bancho
    source: str
    status: int
    tags: str
    title: str

class Beatmap(TypedDict):
    
    beatmapset: Beatmapset
    ar: float
    bpm: float
    created_at: str
    cs: float
    diff: float
    filename: str
    hp: float
    id: int
    last_update: str
    max_combo: int
    md5: str
    mode: int
    od: float
    passcount: int
    playcount: int
    set_id: int
    status: int
    total_length: int
    version: str
    
class Score(TypedDict):

    beatmap: Beatmap
    acc: float
    grade: str
    id: int
    max_combo: int
    mode: int
    mods: int
    n300: int
    n100: int
    n50: int
    nGeki: int
    nKatu: int
    nMiss: int
    perfect: bool
    pinned: bool
    pp: float
    submitted_at: str
    total_score: int
    user_id: int    

class MostPlayed(TypedDict):
    beatmap: Beatmap
    count: int

class LeaderboardUser(TypedDict):
    pp: float
    rank: int
    user: Profile
    user_id: int

def lookup_user(username: str) -> int | None:
    req = handler.get(f"https://osu.lekuru.xyz/u/{username}")
    if not req.ok:
        return
    return int(req.url.split("/")[-1])

def get_user_info(user_id: int) -> Profile | None:
    req = handler.get(f"https://osu.lekuru.xyz/api/profile/{user_id}")
    if not req.ok:
        return
    return req.json()

def get_user_recent(user_id: int, mode: int) -> List[Score] | None:
    req = handler.get(f"https://osu.lekuru.xyz/api/profile/{user_id}/recent/{modes[mode]}")
    if not req.ok:
        return
    return req.json()

def get_user_first_places(user_id: int, mode: int, length=50, page=1) -> List[Score] | None:
    req = handler.get(f"https://osu.lekuru.xyz/api/profile/{user_id}/first/{modes[mode]}?limit={length}&offset={(page-1)*length}")
    if not req.ok:
        return
    return req.json()

def get_user_most_played(user_id: int, length=50, page=1) -> List[MostPlayed] | None:
    req = handler.get(f"https://osu.lekuru.xyz/api/profile/{user_id}/plays?limit={length}&offset={(page-1)*length}")
    if not req.ok:
        return
    return req.json()

def get_user_top(user_id: int, mode: int, length=50, page=1) -> List[Score] | None:
    req = handler.get(f"https://osu.lekuru.xyz/api/profile/{user_id}/top/{modes[mode]}?limit={length}&offset={(page-1)*length}")
    if not req.ok:
        return
    return req.json()

def get_user_lb(mode: int, type: LeaderboardType = LeaderboardType.pp, length=50, page=1) -> List[LeaderboardUser] | None:
    req = handler.get(f"https://osu.lekuru.xyz/api/rankings/{type.value}/{modes[mode]}?limit={length}&offset={(page-1)*length}")
    if not req.ok:
        return
    return req.json()
