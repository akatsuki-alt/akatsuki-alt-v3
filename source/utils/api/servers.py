
class Server:
    
    def __init__(self, server_name: str, server_url: str, supports_rx: bool, supports_ap: bool, notes: str) -> None:
        self.server_name = server_name
        self.server_url = server_url
        self.supports_rx = supports_rx
        self.supports_ap = supports_ap
        self.notes = notes
        
servers = [Server('akatsuki', 'https://akatsuki.gg', supports_rx=True, supports_ap=True, notes="Full support")]
