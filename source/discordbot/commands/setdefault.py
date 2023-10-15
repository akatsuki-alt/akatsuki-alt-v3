from utils.database import DBDiscordLink

from utils.api.servers import servers
from utils.parser import parse_args

from discord import Message, Embed
from discordbot.bot import Command

import utils.postgres as postgres
from typing import *

class SetDefaultCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("setdefault", "Set default gamemode/server", ["setdefault", "default"], "arguments: [gamemode] [server]")
    
    async def run(self, message: Message, arguments: List[str]):
        server_link = servers[0]
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        args = parse_args(arguments, unparsed=True)
        if not args['unparsed']:
            await message.reply(f"Specify a gamemode!")
            return
        if args['unparsed'][0] not in modes:
            await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
            return
        mode, relax = modes[args['unparsed'][0]]
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
        with postgres.instance.managed_session() as session:
            if (dblink := session.get(DBDiscordLink, message.author.id)) is None:
                await message.reply("Please link an account!")
                return
            if server_link.server_name not in dblink.servers:
                await message.reply("You don't have an account linked for that server!")
                return
            dblink.default_mode = mode
            dblink.default_relax = relax
            dblink.default_server = server_link.server_name
            await message.reply(f"Your default is now {args['unparsed'][0]} with server {server_link.server_name}")
            session.merge(dblink)
            session.commit()