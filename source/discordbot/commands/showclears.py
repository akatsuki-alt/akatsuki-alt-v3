from discord import Message, Embed, ButtonStyle, Interaction
from utils.api.akatsukialt.akataltapi import ScoreSortEnum
from discord.ui import View, button, Button
from utils.api.akataltapi import instance
from utils.beatmaps import load_beatmap
from utils.mods import get_mods_simple
from utils.parser import parse_args
from discordbot.bot import Command
from typing import List

import utils.postgres as postgres

class ClearsView(View):
    
    def __init__(self, api_options, all=False):
        super().__init__()
        self.types = [e.value for e in ScoreSortEnum]
        self.type = 4
        self.desc = True
        self.api_options = api_options
        self.all = all
        self.page = 1
    
    @button(label="Previous", style=ButtonStyle.gray)
    async def prev_button(self, interaction: Interaction, button: Button):
        await interaction.response.defer()   
        self.page = max(self.page-1, 1)
        await interaction.message.edit(embed=self.get_embed(), view=self)

    @button(label="Next", style=ButtonStyle.gray)
    async def next_button(self, interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.page += 1
        await interaction.message.edit(embed=self.get_embed(), view=self)
 
    @button(label="Sort: pp", style=ButtonStyle.gray)
    async def toggle_type(self, interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.type += 1
        if self.type == len(self.types):
            self.type = 0
        self.page = 1
        button.label = f"Sort: {self.types[self.type]}"
        await interaction.message.edit(embed=self.get_embed(), view=self)
    
    @button(label="Order: ↓", style=ButtonStyle.gray)
    async def toggle_desc(self, interaction: Interaction, button: Button):
        await interaction.response.defer()   
        if self.desc:
            self.desc = False
            button.label = "Order: ↑"
        else:
            self.desc = True
            button.label = "Order: ↓"
        self.page = 1
        await interaction.message.edit(embed=self.get_embed(), view=self)

    @button(label="Download", style=ButtonStyle.green)
    async def download_button(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        if self.all:
            links = instance.get_all_clears(
                server=self.api_options['server'],
                mode=self.api_options['mode'],
                relax=self.api_options['relax'],
                sort=self.types[self.type],
                desc=self.desc,
                score_filter=self.api_options['score_filter'],
                beatmap_filter=self.api_options['beatmap_filter'],
            )
        else:
            links = instance.get_user_clears(
                user_id=self.api_options['user_id'],
                server=self.api_options['server'],
                mode=self.api_options['mode'],
                relax=self.api_options['relax'],
                sort=self.types[self.type],
                desc=self.desc,
                score_filter=self.api_options['score_filter'],
                beatmap_filter=self.api_options['beatmap_filter'],
                download_link=True
            )
        embed = Embed(title="Download options:", 
                      description="\n".join([f"[{key}]({value})" for (key,value) in links.items()]))
        await interaction.followup.send(embed=embed)


    def get_embed_user(self):
        embed = Embed(title="Clears")
        scores = instance.get_user_clears(
            user_id=self.api_options['user_id'],
            server=self.api_options['server'],
            mode=self.api_options['mode'],
            relax=self.api_options['relax'],
            sort=self.types[self.type],
            page=self.page,
            length=10,
            desc=self.desc,
            score_filter=self.api_options['score_filter'],
            beatmap_filter=self.api_options['beatmap_filter'],
        )
        content = '```'
        if not scores or not scores[1]:
            content += 'No scores :(\n```'
            embed.description = content
            return embed
        embed.title += f" ({scores[0]:,})"
        with postgres.instance.managed_session() as session:
            for score in scores[1]:
                if (beatmap := load_beatmap(session, score.beatmap_id)) is not None:
                    title = f"{beatmap.artist} - {beatmap.title} [{beatmap.version}]"
                    max_combo = beatmap.max_combo
                else:
                    title = "API error :("
                    max_combo = 42069
                content += f"{title} +{''.join(get_mods_simple(score.mods))}\n"
                content += f"{score.rank} {score.combo}/{max_combo}x [{score.count_300}/{score.count_100}/{score.count_50}/{score.count_miss}] {score.accuracy:.2f}% {score.score:,} {score.pp}pp\n"
        content += '```'
        embed.description = content
        return embed
    
    def get_embed_all(self):
        embed = Embed(title="Clears")
        scores = instance.get_all_clears(
            server=self.api_options['server'],
            mode=self.api_options['mode'],
            relax=self.api_options['relax'],
            sort=self.types[self.type],
            page=self.page,
            length=10,
            desc=self.desc,
            score_filter=self.api_options['score_filter'],
            beatmap_filter=self.api_options['beatmap_filter'],
        )
        content = '```'
        if not scores or not scores[1]:
            content += 'No scores :(\n```'
            embed.description = content
            return embed
        embed.title += f" ({scores[0]:,})"
        with postgres.instance.managed_session() as session:
            for score in scores[1]:
                if (beatmap := load_beatmap(session, score.beatmap_id)) is not None:
                    username = "Unknown Player:"
                    if (user := instance.get_user_info(server=self.api_options['server'], user_id=score.user_id)):
                        username = user.username
                    title = f"{username}: {beatmap.title} [{beatmap.version}]"
                    max_combo = beatmap.max_combo
                else:
                    title = "API error :("
                    max_combo = 42069
                content += f"{title} +{''.join(get_mods_simple(score.mods))}\n"
                content += f"{score.rank} {score.combo}/{max_combo}x [{score.count_300}/{score.count_100}/{score.count_50}/{score.count_miss}] {score.accuracy:.2f}% {score.score:,} {score.pp}pp\n"
        content += '```'
        embed.description = content
        return embed
    
    def get_embed(self):
        if self.all:
            return self.get_embed_all()
        else:
            return self.get_embed_user()
    
    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)

class ShowClearsCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("showclears", "shows a player clears", ['showclears', 'sc'])
    
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments, unparsed=True)
        if (link := self.get_link(message)) is None:
            await message.reply(f"You don't have an account linked!")
            return
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        user_id = link.servers[link.default_server]
        mode = link.default_mode
        relax = link.default_relax
        server = link.default_server
        score_filter = ''
        beatmap_filter = ''
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
        if 'server' in parsed:
            if (server := self.get_server(parsed['server'])) is None:
                await message.reply("Unknown server!")
                return
            server = server.server_name
        if 'user' in parsed:
            lookup = self.get_server(server).lookup_user(parsed['user'])
            if not lookup:
                await message.reply(f"User not found!")
                return
            user_id = lookup[1]
        if 'score_filter' in parsed:
            score_filter = parsed['score_filter']
        if 'beatmap_filter' in parsed:
            beatmap_filter = parsed['beatmap_filter']
        await ClearsView({'user_id': user_id, 'server': server, 'mode': mode, 'relax': relax, 'score_filter': score_filter, 'beatmap_filter': beatmap_filter}).reply(message)

class ShowServerClearsCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("showserverclears", "shows every clears", ['showserverclears', 'serverclears'])
    
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments, unparsed=True)
        if (link := self.get_link(message)) is None:
            await message.reply(f"You don't have an account linked!")
            return
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        mode = link.default_mode
        relax = link.default_relax
        server = link.default_server
        score_filter = ''
        beatmap_filter = ''
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
        if 'server' in parsed:
            if (server := self.get_server(parsed['server'])) is None:
                await message.reply("Unknown server!")
                return
            server = server.server_name
        if 'score_filter' in parsed:
            score_filter = parsed['score_filter']
        if 'beatmap_filter' in parsed:
            beatmap_filter = parsed['beatmap_filter']
        await ClearsView(all=True, api_options={'server': server, 'mode': mode, 'relax': relax, 'score_filter': score_filter, 'beatmap_filter': beatmap_filter}).reply(message)