from typing import List, Union

from osu import Game
from osu.objects import Channel, Player
from gamebot.bot import Command, ContextEnum

class PingCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("ping", "return pong", "return pong", ["ping"], ["ANY"], ContextEnum.PRIVATE)
    
    def run(self, game: Game, sender: Player, target: Player | Channel, context: ContextEnum, message: str, arguments: List[str]):
        sender.send_message("pong!")
