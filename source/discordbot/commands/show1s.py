from discord import Message, ButtonStyle, Interaction, Embed
from utils.api.akatsukialt.akataltapi import ScoreSortEnum
from discord.ui import View, Button, button
from utils.api.akataltapi import instance
from utils.beatmaps import load_beatmap
from utils.mods import get_mods_simple
from discordbot.bot import Command
from utils.parser import parse_args
from typing import List

import utils.postgres as postgres

class FirstPlacesView(View):
    
    def __init__(self, api_options):
        self.types = ['all', 'new', 'lost']
        self.types_sort = [e.value for e in ScoreSortEnum]
        self.type = 0
        self.type_sort = 4
        self.desc = True
        self.api_options = api_options
        self.page = 1
        super().__init__()

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
 
    @button(label="Type: all", style=ButtonStyle.gray)
    async def toggle_type(self, interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.type += 1
        if self.type == len(self.types):
            self.type = 0
        self.page = 1
        button.label = f"Type: {self.types[self.type]}"
        await interaction.message.edit(embed=self.get_embed(), view=self)

    @button(label="Sort: pp", style=ButtonStyle.gray)
    async def toggle_sort_type(self, interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.type_sort += 1
        if self.type_sort == len(self.types_sort):
            self.type_sort = 0
        self.page = 1
        button.label = f"Sort: {self.types_sort[self.type_sort]}"
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
        links = instance.get_user_1s(
            user_id = self.api_options['user_id'],
            server = self.api_options['server'],
            mode = self.api_options['mode'],
            relax = self.api_options['relax'],
            type = self.types[self.type],
            sort=self.types_sort[self.type_sort],
            desc=self.desc,
            score_filter=self.api_options['score_filter'],
            beatmap_filter=self.api_options['beatmap_filter'],
            download_link=True
        )
        embed = Embed(title="Download options:", 
                      description="\n".join([f"[{key}]({value})" for (key,value) in links.items()]))
        await interaction.followup.send(embed=embed)


    def get_embed(self):
        embed = Embed(title=f"First places")
        content = '```'
        with postgres.instance.managed_session() as session:
            first_places = instance.get_user_1s(
                user_id = self.api_options['user_id'],
                server = self.api_options['server'],
                mode = self.api_options['mode'],
                relax = self.api_options['relax'],
                type = self.types[self.type],
                sort=self.types_sort[self.type_sort],
                desc=self.desc,
                score_filter=self.api_options['score_filter'],
                beatmap_filter=self.api_options['beatmap_filter'],
                page = self.page,
                length = 10
            )
            if not first_places or not first_places[1]:
                content += "No scores :/```"
                embed.description = content
                return embed
            embed.title += f" ({first_places[0]:,})"
            for first_place in first_places[1]:
                if (beatmap := load_beatmap(session, first_place.beatmap_id)) is not None:
                    title = f"{beatmap.artist} - {beatmap.title} [{beatmap.version}]"
                    max_combo = beatmap.max_combo
                else:
                    title = "API error :("
                    max_combo = 42069
                content += f"{title} +{''.join(get_mods_simple(first_place.mods))}\n"
                content += f"{first_place.rank} {first_place.combo}/{max_combo}x [{first_place.count_300}/{first_place.count_100}/{first_place.count_50}/{first_place.count_miss}] {first_place.accuracy:.2f}% {first_place.pp}pp\n"
        content += '```'
        embed.description = content
        return embed

    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)

class AllFirstPlacesView(View):
    
    def __init__(self, api_options):
        self.types_sort = [e.value for e in ScoreSortEnum]
        self.type_sort = 4
        self.desc = True
        self.api_options = api_options
        self.page = 1
        super().__init__()

    @button(label="Previous", style=ButtonStyle.gray)
    async def prev_button(self, interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.page = max(self.page-1, 1)
        await interaction.message.edit(embed=self.get_embed(), view=self)

    @button(label="Next", style=ButtonStyle.gray)
    async def next_button(self,  interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.page += 1
        await interaction.message.edit(embed=self.get_embed(), view=self)
 
    @button(label="Sort: pp", style=ButtonStyle.gray)
    async def toggle_sort_type(self, interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.type_sort += 1
        if self.type_sort == len(self.types_sort):
            self.type_sort = 0
        self.page = 1
        button.label = f"Sort: {self.types_sort[self.type_sort]}"
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
    async def download_button(self, interaction:Interaction, button: Button):
        await interaction.response.defer()
        links = instance.get_all_1s(
            server = self.api_options['server'],
            mode = self.api_options['mode'],
            relax = self.api_options['relax'],
            sort=self.types_sort[self.type_sort],
            desc=self.desc,
            score_filter=self.api_options['score_filter'],
            beatmap_filter=self.api_options['beatmap_filter'],
            download_link=True
        )
        embed = Embed(title="Download options:", 
                      description="\n".join([f"[{key}]({value})" for (key,value) in links.items()]))
        await interaction.followup.send(embed=embed)


    def get_embed(self):
        embed = Embed(title=f"First places")
        content = '```'
        with postgres.instance.managed_session() as session:
            first_places = instance.get_all_1s(
                server = self.api_options['server'],
                mode = self.api_options['mode'],
                relax = self.api_options['relax'],
                sort=self.types_sort[self.type_sort],
                desc=self.desc,
                score_filter=self.api_options['score_filter'],
                beatmap_filter=self.api_options['beatmap_filter'],
                page = self.page,
                length = 10
            )
            if not first_places or not first_places[1]:
                content += "No scores :/```"
                embed.description = content
                return embed
            embed.title += f" ({first_places[0]})"
            for score in first_places[1]:
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

    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)


class Show1sCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("show1s", "show first places", ['show1s'])
    
    async def run(self, message: Message, arguments: List[str]):
        if (link := self.get_link(message)) is None:
            await message.reply(f"You don't have an account linked1")
            return
        parsed = parse_args(arguments, unparsed=True)
        user_id = link.servers[link.default_server]
        mode = link.default_mode
        relax = link.default_relax
        server = link.default_server
        score_filter = ''
        beatmap_filter = ''
        if 'server' in parsed:
            if (server := self.get_server(parsed['server'])) is None:
                await message.reply("Unknown server!")
                return
            server = server.server_name
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
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
        await FirstPlacesView({'user_id': user_id, 
                               'server': server,
                               'mode': mode,
                               'relax': relax,
                               'score_filter': score_filter,
                               'beatmap_filter': beatmap_filter
                            }).reply(message)

class ShowServer1sCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("showserver1s", "shows every first places", ['showserver1s', 'server1s'])
    
    async def run(self, message: Message, arguments: List[str]):
        if (link := self.get_link(message)) is None:
            await message.reply(f"You don't have an account linked1")
            return
        parsed = parse_args(arguments, unparsed=True)
        mode = link.default_mode
        relax = link.default_relax
        server = link.default_server
        score_filter = ''
        beatmap_filter = ''
        if 'server' in parsed:
            if (server := self.get_server(parsed['server'])) is None:
                await message.reply("Unknown server!")
                return
            server = server.server_name
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
        if 'score_filter' in parsed:
            score_filter = parsed['score_filter']
        if 'beatmap_filter' in parsed:
            beatmap_filter = parsed['beatmap_filter']
        await AllFirstPlacesView({
                               'server': server,
                               'mode': mode,
                               'relax': relax,
                               'score_filter': score_filter,
                               'beatmap_filter': beatmap_filter
                            }).reply(message)
        
