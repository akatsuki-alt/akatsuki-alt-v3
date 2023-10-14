from utils.api.servers import servers
from discord import Message, Embed
from discordbot.bot import Command
from typing import *

class ServersCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("Servers", "shows current supported servers", ["servers"])
    
    async def run(self, message: Message, arguments: List[str]):
        embed = Embed(title="Servers supported")
        embed.description = '```'
        for server in servers:
            embed.description += f"""{server.server_name.title()}: {server.server_url}
  Supports RX: {'yes' if server.supports_rx else 'no'}
  Supports AP: {'yes' if server.supports_ap else 'no'}
  Notes: {server.notes}
"""
        embed.description += '```'
        await message.reply(embed=embed)        