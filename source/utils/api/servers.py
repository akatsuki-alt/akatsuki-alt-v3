from typing import List, Tuple, Union

import utils.api.akatsuki as akatsuki
import utils.api.titanic as titanic
from typing import *

class Server:
    
    def __init__(self, server_name: str, server_url: str, beatmap_sets: List[str], supports_rx: bool, supports_ap: bool, notes: str) -> None:
        self.server_name = server_name
        self.server_url = server_url
        self.beatmap_sets = beatmap_sets
        self.supports_rx = supports_rx
        self.supports_ap = supports_ap
        self.notes = notes
    
    def lookup_user(self, user: Union[str, int]) -> Tuple[str, int]:
        pass
    
    def get_pfp(self, user: int) -> str:
        return "https://external-preview.redd.it/STe7DUG0S90McIj6VAPErso141_cmtEjPJkBGn9eTJw.png?auto=webp&s=94ee7479ec8d4ebc4c6c7a3971b32a73bfa1d81b"

    def get_recent(self, user: int, mode: int, relax: int) -> akatsuki.Score | None:
        return

class Akatsuki(Server):
    
    def __init__(self) -> None:
        super().__init__('akatsuki', 'https://akatsuki.gg', ['akatsuki', 'bancho'], supports_rx=True, supports_ap=True, notes="Full support")

    def lookup_user(self, user: str | int) -> Tuple[str, int] | None:
        if type(user) == int or user.isnumeric():
            user_info = akatsuki.get_user_info(int(user))
            if not user_info:
                return None
            return user_info['username'], user_info['id']
        else:
            return akatsuki.lookup_user(user)

    def get_pfp(self, user: int) -> str:
        return f"https://a.akatsuki.gg/{user}"

    def get_recent(self, user: int, mode: int, relax: int) -> akatsuki.Score | None:
        if (recent := akatsuki.get_user_recent(user_id=user, mode=mode, relax=relax, length=1)):
            return recent[0]

class Titanic(Server):
    
    def __init__(self) -> None:
        super().__init__("titanic", "https://osu.lekuru.xyz", ["titanic"], False, False, "Basic support")

    def lookup_user(self, user: str | int) -> Tuple[str, int]:
        if type(user) == int or user.isnumeric():
            user_info = titanic.get_user_info(int(user))
            if not user_info:
                return None
            return user_info['name'], user_info['id']
        else:
            id = titanic.lookup_user(user)
            if id:
                return user, id

    def get_pfp(self, user: int) -> str:
        return f"https://osu.lekuru.xyz/a/{user}?h=120"

    def get_recent(self, user: int, mode: int, relax: int) -> akatsuki.Score | None:
         if (recent := titanic.get_user_recent(user_id=user, mode=mode)):
            if recent[0]:
                return {'id': recent[0]['id'], 
                        'score': recent[0]['total_score'],
                        'max_combo': recent[0]['max_combo'],
                        'full_combo': recent[0]['perfect'],
                        'mods': recent[0]['mods'],
                        'count_300': recent[0]['n300'],
                        'count_100': recent[0]['n100'],
                        'count_50': recent[0]['n50'],
                        'count_geki': recent[0]['nGeki'],
                        'count_katu': recent[0]['nKatu'],
                        'count_miss': recent[0]['nMiss'],
                        'accuracy': recent[0]['acc']*100,
                        'pp': recent[0]['pp'],
                        'rank': recent[0]['grade'],
                        'pinned': recent[0]['pinned'],
                        'play_mode': recent[0]['mode'],
                        'completed': 3, # TODO
                        'beatmap': {'beatmap_id': recent[0]['beatmap']['id']},
                        'time': recent[0]['submitted_at']
                        }

servers = [Akatsuki(), Titanic()]
