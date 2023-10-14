from osu.bancho.constants import ServerPackets
from osu.objects import Player, Channel
from threading import Thread
from enum import Enum
from typing import *
from osu import Game

class ContextEnum(Enum):

    CHANNEL = "channel"
    PRIVATE = "private"
    ALL = "all"

class Command:
    
    def __init__(self, name: str, description: str, help: str, triggers: List[str], servers: List[str], context: ContextEnum) -> None:
        self.name = name
        self.description = description
        self.help = help
        self.triggers = triggers
        self.servers = servers
        self.context = context
    
    async def run(self, game: Game, sender: Player, target: Union[Player, Channel], context: ContextEnum, message: str, arguments: List[str]):
        pass

class Client:
    
    def __init__(self, username: str, password: str, server: str) -> None:
        self.gameclient = Game(username=username, password=password, server=server)
        self.outer_on_message()
        self.thread = Thread(target=self.start_loop)
        self.thread.start()

    def outer_on_message(self):
        @self.game.events.register(ServerPackets.SEND_MESSAGE)
        def on_message(sender: Player, message: str, target: Union[Player, Channel]):
 
            if not (message := message.strip()).startswith("!"):
                return
 
            self.logger.info(f"{sender} executed a command: {message}")
            trigger, *args = message[1:].split()
            trigger = trigger.lower()
            context = ContextEnum.CHANNEL if type(Channel) else ContextEnum.PRIVATE
            
            for command in commands:
                if trigger in command.triggers:
                    if command.context != ContextEnum.ALL and command.context != context:
                        continue
                    if "ANY" not in command.servers and self.gameclient.server not in command.servers:
                        continue
                    command.run(self.gameclient, sender, target, context, message, args)
                    return

            if context != ContextEnum.CHANNEL:
                sender.send_message("Unknown command!")


    def start_loop(self):
        self.gameclient.run(retry=True, exit_on_interrupt=True)

commands: List[Command] = list()

def main():
    pass