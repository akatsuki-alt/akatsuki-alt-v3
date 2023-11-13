from utils.api.request import RequestHandler
from typing import *

handler = RequestHandler(req_min=60)

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

