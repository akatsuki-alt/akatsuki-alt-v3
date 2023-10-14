from discord.flags import Intents
from discord import Message
from typing import *

import discord
import config
import shlex

class Command:
    
    def __init__(self, name: str, description: str, triggers: List[str], help: str = "no help available.") -> None:
        self.name = name
        self.description = description
        self.help = help
        self.triggers = triggers
    
    async def run(self, message: Message, arguments: List[str]):
        pass

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
            for command in self.commands:
                if split[0] in command.triggers:
                    try:
                        await command.run(message, split[1:])
                    except:
                        pass
            
intents = discord.Intents.default()
intents.message_content = True
commands: List[Command] = list()
client: Client = None

def main():
    global client
    client = Client(intents=intents, commands=commands)
    client.run(config.DISCORD_BOT_TOKEN)