from utils.database import DBUserQueue, DBUserInfo
from datetime import date, timedelta
from utils.parser import parse_args
from discordbot.bot import Command
from discord import Message
from typing import List

import utils.postgres as postgres

class AddQueueCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("addqueue", "Adds a player to queue", ["addqueue"])
    
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments, unparsed=True)
        if (link := self.get_link(message)) is None:
            await self.show_link_warning(message)
            return
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        if len(parsed['unparsed']) < 2:
            await message.reply("Specify a player and a gamemode!")
            return
        username = parsed['unparsed'][0]
        if parsed['unparsed'][1] not in modes:
            await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
            return
        mode, relax = modes[parsed['unparsed'][1]]
        server_name = parsed['server'] if 'server' in parsed else link.default_server
        if (server := self.get_server(server_name)) is None:
            await message.reply("Server not found!") # TODO: make generalised message function
            return
        if (lookup := server.lookup_user(username)) is None:
            await message.reply("User not found!")
            return
        with postgres.instance.managed_session() as session:
            if session.query(DBUserInfo).filter(DBUserInfo.server == server.server_name, DBUserInfo.user_id == lookup[1], DBUserInfo.mode == mode, DBUserInfo.relax == relax).first():
                await message.reply("User already processed!")
                return
            session.merge(DBUserQueue(server=server.server_name, user_id=lookup[1], mode=mode, relax=relax, date=(date.today()-timedelta(days=1))))
            session.commit()
            await message.reply("User added in queue.")
        