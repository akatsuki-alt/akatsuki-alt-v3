import utils.api.akatsuki as akatsuki
from typing import *

class Server:
    
    def __init__(self, server_name: str, server_url: str, supports_rx: bool, supports_ap: bool, notes: str) -> None:
        self.server_name = server_name
        self.server_url = server_url
        self.supports_rx = supports_rx
        self.supports_ap = supports_ap
        self.notes = notes
    
    def lookup_user(self, user: Union[str, int]):
        pass

class Akatsuki(Server):
    
    def __init__(self) -> None:
        super().__init__('akatsuki', 'https://akatsuki.gg', supports_rx=True, supports_ap=True, notes="Full support")

    def lookup_user(self, user: str | int) -> Tuple[str, int] | None:
        if type(user) == int:
            user_info = akatsuki.get_user_info(user)
            if not user_info:
                return None
            return user_info['username'], user_info['id']
        else:
            return akatsuki.lookup_user(user)


servers = [Akatsuki()]
