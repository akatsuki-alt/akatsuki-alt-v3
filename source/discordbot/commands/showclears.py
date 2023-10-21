from typing import List, Optional

from discord import Message, Embed
from discordbot.bot import Command
import discord
from utils.parser import parse_args
from utils.api.akataltapi import instance
from utils.api.akatsukialt.akataltapi import ScoreSortEnum
import utils.postgres as postgres
from utils.beatmaps import load_beatmap
from utils.mods import get_mods_simple

class ClearsView(discord.ui.View):
    
    def __init__(self, api_options):
        super().__init__()
        self.types = [e.value for e in ScoreSortEnum]
        self.type = 4
        self.desc = True
        self.api_options = api_options
        self.page = 1
    
    @discord.ui.button(label="Previous",style=discord.ButtonStyle.gray)
    async def prev_button(self,  interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.defer()   
        self.page = max(self.page-1, 1)
        await interaction.message.edit(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next",style=discord.ButtonStyle.gray)
    async def next_button(self,  interaction:discord.Interaction, button:discord.ui.Button):    
        await interaction.response.defer()   
        self.page += 1
        await interaction.message.edit(embed=self.get_embed(), view=self)
 
    @discord.ui.button(label="Sort: pp",style=discord.ButtonStyle.gray)
    async def toggle_type(self, interaction:discord.Interaction, button:discord.ui.Button):    
        await interaction.response.defer()   
        self.type += 1
        if self.type == len(self.types):
            self.type = 0
        self.page = 1
        button.label = f"Sort: {self.types[self.type]}"
        await interaction.message.edit(embed=self.get_embed(), view=self)
    
    @discord.ui.button(label="Order: ↓",style=discord.ButtonStyle.gray)
    async def toggle_desc(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.defer()   
        if self.desc:
            self.desc = False
            button.label = "Order: ↑"
        else:
            self.desc = True
            button.label = "Order: ↓"
        self.page = 1
        await interaction.message.edit(embed=self.get_embed(), view=self)

    def get_embed(self):
        embed = Embed(title="Clears")
        scores = instance.get_user_clears(
            user_id=self.api_options['user_id'],
            server=self.api_options['server'],
            mode=self.api_options['mode'],
            relax=self.api_options['relax'],
            sort=self.types[self.type],
            page=self.page,
            length=10,
            desc=self.desc
        )
        content = '```'
        if not scores or not scores[1]:
            content += 'No scores :(\n```'
            embed.description = content
            return embed
        embed.title += f" ({scores[0]})"
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
        await ClearsView({'user_id': user_id, 'server': server, 'mode': mode, 'relax': relax}).reply(message)