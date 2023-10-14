from utils.database import DBDiscordLink

from utils.api.servers import servers
from utils.parser import parse_args

from discord import Message, Embed
from discordbot.bot import Command

import utils.postgres as postgres
from typing import *

class LinkCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("Link", "Link game account to your discord", ["link"])
    
    async def run(self, message: Message, arguments: List[str]):
        server_link = servers[0]
        args = parse_args(arguments, unparsed=True)
        if not args['unparsed']:
            await message.reply(f"Specify an UserID/Username!")
            return
        if len(args['unparsed']) > 1:
            found = False
            for server in servers:
                if server.server_name.lower() == args['unparsed'][1].lower():
                    server_link = server
                    found = True
                    break
            if not found:
                await message.reply(f"Unknown server! Use !servers for a list of servers.")
                return
        lookup = server_link.lookup_user(args['unparsed'][0])
        if not lookup:
            await message.reply(f"User was not found on the server!")
            return
        with postgres.instance.managed_session() as session:
            if (dblink := session.get(DBDiscordLink, message.author.id)) is None:
                dblink = DBDiscordLink(discord_id = message.author.id)
                dblink.default_server = server_link.server_name
            if not dblink.servers:
                dblink.servers = {}
            dblink.servers[server_link.server_name] = lookup[1]
            session.merge(dblink)
            session.commit()
            await message.reply(f"Linked as {lookup[0]} on {server_link.server_name}!")
