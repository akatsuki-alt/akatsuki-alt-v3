from utils.api.servers import servers, Server
from utils.database import DBDiscordLink
from difflib import SequenceMatcher
from utils.logger import get_logger
from discord.flags import Intents
from discord import Message
from typing import *

import utils.postgres as postgres
import discord
import config
import shlex

logger = get_logger("discord_bot")

class Command:
    
    def __init__(self, name: str, description: str, triggers: List[str], help: str = "no help available.") -> None:
        self.name = name
        self.description = description
        self.help = help
        self.triggers = triggers
    
    async def run(self, message: Message, arguments: List[str]):
        pass
    
    def get_link(self, message: Message) -> DBDiscordLink | None:
        with postgres.instance.managed_session() as session:
            return session.get(DBDiscordLink, (message.author.id))

    async def show_link_warning(self, message: Message):
        await message.reply(f"You don't have an account linked!")
        
    def get_server(self, server_name: str) -> Server | None:
        for server in servers:
            if server.server_name.lower() == server_name.lower():
                return server
    
class Client(discord.Client):

    def __init__(self, intents: Intents, commands: List[Command], prefix="!") -> None:
        self.prefix = prefix
        self.commands = commands
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: Message):
        if message.author.id == self.user.id:
            return
        if message.content.startswith("!"):
            split = shlex.split(message.content[1:])
            most_similar = (0, 'none')
            for command in self.commands:
                if split[0] in command.triggers:
                    try:
                        await command.run(message, split[1:])
                        return
                    except:
                        logger.error(f"Failed to execute {message.content}!", exc_info=True)
                else:
                    for trigger in command.triggers:
                        if (ratio := SequenceMatcher(None, trigger, split[0]).ratio()) > most_similar[0]:
                            most_similar = (ratio, trigger)
            await message.reply(f"Unknown command! Did you mean {most_similar[1]}?")

intents = discord.Intents.default()
intents.message_content = True
commands: List[Command] = list()
client: Client = None

def main():
    global client
    client = Client(intents=intents, commands=commands)
    client.run(config.DISCORD_BOT_TOKEN)