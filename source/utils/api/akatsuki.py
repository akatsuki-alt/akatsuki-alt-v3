from utils.api.request import RequestHandler
from enum import Enum
from typing import *

handler = RequestHandler(req_min=200)

class GamemodeString(Enum):
    std = 0
    taiko = 1
    ctb = 2
    mania = 3

class SortOption(Enum):
    PP = 0
    SCORE = 1
    ALL = 2

class ChosenMode(TypedDict):
    ranked_score: int
    total_score: int
    playcount: int
    playtime: int
    replays_watched: int
    total_hits: int
    level: float
    accuracy: float
    pp: int
    global_leaderboard_rank: int
    country_leaderboard_rank: int
    max_combo: int

class Beatmap(TypedDict):
    beatmap_id: int
    beatmapset_id: int
    beatmap_md5: str
    song_name: str
    ar: float
    od: float
    difficulty: float # super broken
    difficulty2: Dict[GamemodeString, float] # same
    max_combo: int
    hit_length: int
    ranked: int
    ranked_status_freezed: int
    latest_update: str

class Badge(TypedDict):
    id: int
    name: str
    icon: str

class SilenceInfo(TypedDict):
    reason: str
    end: str

class Clan(TypedDict):
    id: int
    name: str
    tag: str
    description: str
    icon: str
    owner: int
    status: int

class User(TypedDict):
    id: int
    username: str
    username_aka: str
    registered_on: str
    privileges: int
    latest_activity: str
    country: str
    play_style: int
    favourite_mode: int
    stats: List[Dict[GamemodeString, ChosenMode]]
    followers: int
    clan: Clan
    badges: List[Badge]
    tbadges: List[Badge]
    custom_badge: Badge
    silence_info: SilenceInfo

class Score(TypedDict):
    id: str # not a bug
    beatmap_md5: str
    score: int
    max_combo: int
    full_combo: bool
    mods: int
    count_300: int
    count_100: int
    count_50: int
    count_geki: int
    count_katu: int
    count_miss: int
    time: str
    play_mode: int
    accuracy: float
    pp: float
    rank: Union[str, int] # ???
    completed: int
    pinned: bool
    beatmap: Beatmap

class MostPlayedMap(TypedDict):
    playcount: int
    beatmap: Beatmap

def initialise_dict(data, typed_dict: TypedDict):
    result = typed_dict()
    for key in data:
        if key not in typed_dict.__annotations__:
            print(f"{key} not found on {typed_dict.__class__.__name__}!")
        else:
            result[key] = data[key]
    return result

def non_zero_dict(dict: dict, ignore_keys: list = []):
    for key in dict:
        if key in ignore_keys:
            continue
        if dict[key]:
            return True
    return False

def get(url):
    req = handler.get(url)
    # TODO: log requests
    if req.ok:
        return req.json()

def get_leaderboard(mode=0, relax=0, pages=1, sort: SortOption = SortOption.PP) -> List[Tuple[User, ChosenMode]]:
    res = list()
    page = 1
    country_rank = {}
    rank = 0
    types = ['pp', 'score', 'magic']
    type = types[sort.value]
    def get_country_rank(country):
        if country not in country_rank:
            country_rank[country] = 0
        country_rank[country] += 1
        return country_rank[country]
    while True:
        req = get(f"https://akatsuki.gg/api/v1/leaderboard?mode={mode}&p={page}&l=500&rx={relax}&sort={type}")
        if not req:
            break
        if not req['users']:
            break
        for user in req['users']:
            rank+=1
            chosen_mode = user['chosen_mode']
            del user['chosen_mode']
            user_dict = initialise_dict(user, User)
            chosen_mode_dict = initialise_dict(chosen_mode, ChosenMode)
            chosen_mode_dict['global_leaderboard_rank'] = rank
            chosen_mode_dict['country_leaderboard_rank'] = get_country_rank(user_dict['country'])
            if non_zero_dict(chosen_mode_dict, ignore_keys=["level", "global_leaderboard_rank", "country_leaderboard_rank"]):
                res.append((user_dict, chosen_mode_dict))
            else:
                return res
        page +=1
        if page>pages:
            break
    return res

def lookup_user(username: str) -> Tuple[str, int] | None:
    req = get(f"https://akatsuki.gg/api/v1/users/lookup?name={username}")
    if not req or not req['users']:
        return
    for user in req['users']:
        if user['username'].lower() == username.lower():
            return user['username'], user['id']

def get_user_info(user_id: int) -> User:
    req = get(f"https://akatsuki.gg/api/v1/users/full?id={user_id}")
    if not req:
        return
    del req['code']
    return initialise_dict(req, User)

def get_user_pinned(user_id: int, mode=0, relax=0, pages=1) -> List[Score]:
    res = list()
    page = 1
    while True:
        req = get(f"https://akatsuki.gg/api/v1/pinned/pinned?mode={mode}&p={page}&l=100&rx={relax}&id={user_id}")
        if not req or not req['scores']:
            break
        for score in req['scores']:
            res.append(initialise_dict(score, Score))
        page+=1
        if page>pages:
            break
    return res

def get_user_most_played(user_id: int, mode=0, relax=0, pages=1) -> List[MostPlayedMap]:
    res = list()
    page = 1
    while True:
        req = get(f"https://akatsuki.gg/api/v1/users/most_played?mode={mode}&p={page}&l=100&rx={relax}&id={user_id}")
        if not req or not req['most_played_beatmaps']:
            break
        for maps in req['most_played_beatmaps']:
            res.append(initialise_dict(maps, MostPlayedMap))
        page+=1
        if page>pages:
            break
    return res

def get_user_best(user_id: int, mode=0, relax=0, pages=1) -> List[Score]:
    res = list()
    page = 1
    while True:
        req = get(f"https://akatsuki.gg/api/v1/users/scores/best?mode={mode}&p={page}&l=100&rx={relax}&id={user_id}")
        if not req or not req['scores']:
            break
        for score in req['scores']:
            res.append(initialise_dict(score, Score))
        page+=1
        if page>pages:
            break
    return res

def get_user_recent(user_id: int, mode=0, relax=0, pages=1, length=100, offset=0) -> List[Score]:
    res = list()
    page = 1
    while True:
        req = get(f"https://akatsuki.gg/api/v1/users/scores/recent?mode={mode}&p={page+offset}&l={length}&rx={relax}&id={user_id}")
        if not req or not req['scores']:
            break
        for score in req['scores']:
            res.append(initialise_dict(score, Score))
        page+=1
        if page>pages:
            break
    return res

def get_user_first_places(user_id: int, mode=0, relax=0, pages=1) -> Tuple[int, List[Score]]:
    res = list()
    total = 0
    page = 1
    while True:
        req = get(f"https://akatsuki.gg/api/v1/users/scores/first?mode={mode}&p={page}&l=100&rx={relax}&id={user_id}")
        total = req['total']
        if not req or not req['scores']:
            break
        for score in req['scores']:
            res.append(initialise_dict(score, Score))
        page+=1
        if page>pages:
            break
    return total, res

def get_map_info(beatmap_id: int) -> Beatmap:
    res = get(f"https://akatsuki.gg/api/v1/beatmaps?b={beatmap_id}")
    return res

def get_clan_first_leaderboard(mode=0, relax=0, pages=1) -> List[Tuple[Clan, int]]:
    page = 1
    clans = list()
    while True:
        req = get(f"https://akatsuki.gg/api/v1/clans/stats/first?m={mode}&p={page}&l=100&rx={relax}")
        if not req['clans']:
            break
        for clan in req['clans']:
            clans.append((clan, clan['count']))
        page += 1
        if page>pages:
            break
    return clans

def get_clan_leaderboard(mode=0, relax=0, pages=1) -> List[Tuple[Clan, ChosenMode]]:
    page = 1
    clans = list()
    while True:
        req = get(f"https://akatsuki.gg/api/v1/clans/stats/all?m={mode}&p={page}&l=100&rx={relax}")
        if not req['clans']:
            break
        for clan in req['clans']:
            clans.append((clan, clan['chosen_mode']))
        page += 1
        if page>pages:
            break
    return clans
