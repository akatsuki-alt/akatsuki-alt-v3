from utils.parser import parse_args
from discordbot.bot import Command
from discord import Message, Embed
from discord.ui import View
from typing import List

import discord

class MapsView(View):
    
    def __init__(self, api_options: dict):
        self.api_options = api_options
        super().__init__()

    def get_embed(self) -> Embed:
        embed = Embed(title="Search result")
        return embed

    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)

class SearchmapsCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("searchmaps", "search beatmaps", ['searchmaps'])
    
    async def run(self, message: Message, arguments: List[str]):
        await MapsView({}).reply(message)