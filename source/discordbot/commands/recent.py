from typing import List

from akatsuki_pp_py import Calculator
from discord import Message, Embed
from discordbot.bot import Command
from utils.parser import parse_args
from utils.beatmaps import load_beatmap, get_calc_beatmap
import utils.postgres as postgres
import utils.mods as mods
from datetime import datetime

class RecentCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("recent", "shows an user's recent play", ['recent', 'r'], "!recent (mode) (user=username) (server=servername)")
    
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments, unparsed=True)
        if (link := self.get_link(message)) is None:
            await message.reply(f"You don't have an account linked!")
            return
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        server = link.default_server
        mode = link.default_mode
        relax = link.default_relax
        user_id = link.servers[server]
        if 'server' in parsed:
            if (server := self.get_server(parsed['server'])) is None:
                await message.reply(f"Unknown server!")
                return
        else:
            server = self.get_server(server)
        if 'user' in parsed:
            if (lookup := server.lookup_user(parsed['user'])) is None:
                await message.reply(f"Can't find user!")
                return
            user_id = lookup[1]
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
        recent = server.get_recent(user_id, mode, relax)
        if not recent:
            await message.reply(f"Player has no recent plays!")
            return
        with postgres.instance.managed_session() as session:
            if (beatmap := load_beatmap(session, recent['beatmap']['beatmap_id'])) is None:
                await message.reply(f"Error occurred loading beatmap.")
                return
        fc_pp = 0
        max_pp = 0
        try:
            calc_map = get_calc_beatmap(beatmap.beatmap_id)
            calc = Calculator(mods = recent['mods'])
            max_pp = int(calc.performance(calc_map).pp)
            calc.set_acc(recent['accuracy'])
            calc.set_n300(recent['count_300'])
            calc.set_n100(recent['count_100'])
            calc.set_n50(recent['count_50'])
            fc_pp = int(calc.performance(calc_map).pp)
        except:
            pass
        lookup = server.lookup_user(user_id)
        embed = Embed(title=f"{beatmap.artist} - {beatmap.title} [{beatmap.version}] +{''.join(mods.get_mods_simple(recent['mods']))}")
        embed.description = f">>{recent['rank']} {recent['max_combo']}/{beatmap.max_combo}x [{recent['count_300']}/{recent['count_100']}/{recent['count_50']}/{recent['count_miss']}] {recent['accuracy']:.2f}% {recent['pp']}pp (FC: {fc_pp}, SS: {max_pp})"
        embed.set_footer(text=f"{lookup[0]} on {server.server_name} at {recent['time']}", icon_url=server.get_pfp(user_id))
        embed.set_thumbnail(url=f"https://assets.ppy.sh/beatmaps/{beatmap.beatmap_id}/covers/cover@2x.jpg")
        await message.reply(embed=embed)
    