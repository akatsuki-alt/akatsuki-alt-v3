from typing import List

from discord import Message
from discordbot.bot import Command

class PingCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("Ping", "debug command", ["ping"])
    
    async def run(self, message: Message, arguments: List[str]):
        await message.reply("pong!")
