from utils.files import DataFile, exists
from utils.parser import parse_args
from discordbot.bot import Command
from discord import Message, Embed
from config import BASE_PATH
from typing import List

import utils.api.akataltapi as akataltapi
import shutil
import time

class ShowCommand(Command):
    
    def __init__(self) -> None:
        help = """
        !show [gamemode] [user=username] [server=servername]
        """
        super().__init__("stats", "show profile statistics", ["show", "stats"], help)
    
    async def run(self, message: Message, arguments: List[str]):
        if (link := self.get_link(message)) is None:
            await self.show_link_warning(message)
            return
        parsed = parse_args(arguments, unparsed=True)
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        user_id = link.servers[link.default_server]
        mode = link.default_mode
        relax = link.default_relax
        server_name = parsed['server'] if 'server' in parsed else link.default_server
        if (server := self.get_server(server_name)) is None:
            await message.reply("Server not found!") # TODO: make generalised message function
            return
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
        if 'user' in parsed:
            lookup = server.lookup_user(parsed['user'])
            if not lookup:
                await message.reply(f"User not found!")
                return
            user_id = lookup[1]
        stats = akataltapi.instance.get_user_statistics(user_id=user_id, server=server_name, mode=mode, relax=relax)
        if not stats:
            await message.reply("API has no stats for user!")
            return
        if not stats.global_score_rank:
            stats.global_score_rank = -1
            stats.country_score_rank = -1
        user_info = akataltapi.instance.get_user_info(user_id=user_id, server=server_name)
        cache_path = f"{BASE_PATH}/cache/{message.author.id}/tracking/{user_id}_{server_name}.json.gz"
        if exists(cache_path):
            cache_file = DataFile(cache_path)
            cache_file.load_data()
        else:
            cache_file = DataFile(cache_path)
            cache_file.data = [(time.time(), (mode, relax), stats.__dict__.copy())]
            del cache_file.data[0][2]['api']
            del cache_file.data[0][2]['date']
            cache_file.save_data()
        last_cached = stats.__dict__.copy()
        del last_cached['api']
        del last_cached['date']
        for cached in cache_file.data:
            if cached[1][0] == mode and cached[1][1] == relax:
                last_cached = cached[2]
                break
        ranked_score = self.get_gain(last_cached['ranked_score'], stats.ranked_score)
        total_score  = self.get_gain(last_cached['total_score'], stats.total_score)
        total_hits   = self.get_gain(last_cached['total_hits'], stats.total_hits)
        play_count = self.get_gain(last_cached['play_count'], stats.play_count)
        play_time = self.get_gain(last_cached['play_time'], stats.play_time)
        replays_watched = self.get_gain(last_cached['replays_watched'], stats.replays_watched)
        level = stats.level - last_cached['level']
        if level:
            level = f"(+{level*100:.2f}%)"
        else:
            level = ""
        accuracy = self.get_gain(last_cached['accuracy'], stats.accuracy)
        max_combo = self.get_gain(last_cached['max_combo'], stats.max_combo)
        global_rank = self.get_gain(last_cached['global_rank'], stats.global_rank, reverse=True)
        country_rank = self.get_gain(last_cached['country_rank'], stats.country_rank, reverse=True)
        pp = self.get_gain(last_cached['pp'], stats.pp)
        global_score_rank = self.get_gain(last_cached['global_score_rank'], stats.global_score_rank, reverse=True)
        country_score_rank = self.get_gain(last_cached['country_score_rank'], stats.country_score_rank, reverse=True)
        first_places = self.get_gain(last_cached['first_places'], stats.first_places)
        clears = self.get_gain(last_cached['clears'], stats.clears)
        current_level = int(stats.level)
        level_percentage = (stats.level - current_level)*100
        embed = Embed(title=f"Statistics for {user_info.username}")
        embed.add_field(name=f"Ranked score", value=f"{stats.ranked_score:,} {ranked_score}")
        embed.add_field(name=f"Total score", value=f"{stats.total_score:,} {total_score}")
        embed.add_field(name=f"Total hits", value=f"{stats.total_hits:,} {total_hits}")
        embed.add_field(name=f"Play count", value=f"{stats.play_count:,} {play_count}")
        embed.add_field(name=f"Play time", value=f"{stats.play_time/60/60:,.2f}h {play_time}")
        embed.add_field(name=f"Replays watched", value=f"{stats.replays_watched:,} {replays_watched}")
        embed.add_field(name=f"Level", value=f"{current_level} +{level_percentage:.2f}% {level}")
        embed.add_field(name=f"Accuracy", value=f"{stats.accuracy:.2f}% {accuracy}")
        embed.add_field(name=f"Max combo", value=f"{stats.max_combo:,}x {max_combo}")
        embed.add_field(name=f"Global Rank", value=f"#{stats.global_rank:,} {global_rank}")
        embed.add_field(name=f"Country Rank", value=f"#{stats.country_rank:,} {user_info.country} {country_rank}")
        embed.add_field(name=f"Performance Points", value=f"{stats.pp:,}pp {pp}")
        embed.add_field(name=f"Global score rank", value=f"#{stats.global_score_rank:,} {global_score_rank}")
        embed.add_field(name=f"Country Rank", value=f"#{stats.country_score_rank:,} {user_info.country} {country_score_rank}")
        embed.add_field(name=f"#1 Count", value=f"{stats.first_places:,} {first_places}")
        embed.add_field(name=f"Clears", value=f"{stats.clears:,} {clears}")
        embed.add_field(name=f"SS+/SS/S+/S", value=f"{stats.xh_count:,}/{stats.x_count:,}/{stats.sh_count:,}/{stats.s_count:,}")
        embed.add_field(name=f"A/B/C/D", value=f"{stats.a_count:,}/{stats.b_count:,}/{stats.c_count:,}/{stats.d_count:,}")
        embed.set_thumbnail(url=server.get_pfp(user_id))
        await message.reply(embed=embed)
    
    def get_gain(self, old, new, float_precision=2, reverse=False):
        if old == new:
            return ""
        if reverse:
            oold = old
            old = new
            new = oold
        res = new-old
        plus = "+" if res > 0 else ""
        if type(res) == float:
            return f"({plus}{res:.{float_precision}f}"
        else:
            return f"({plus}{res:,})"
        
class ResetCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("reset", "Reset your temporary statistics", ['reset'])
    
    async def run(self, message: Message, arguments: List[str]):
        shutil.rmtree(f"{BASE_PATH}/cache/{message.author.id}/tracking/",ignore_errors=True)
        await message.reply(f"Statistics reset.")