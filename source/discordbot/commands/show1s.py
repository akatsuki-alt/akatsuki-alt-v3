from typing import List, Optional

from discord import Message
from discordbot.bot import Command
from utils.parser import parse_args
from utils.api.akataltapi import instance
from utils.beatmaps import load_beatmap
import utils.postgres as postgres
import discord
from utils.mods import get_mods_simple

class FirstPlacesView(discord.ui.View):
    
    def __init__(self, api_options):
        self.types = ['all', 'new', 'lost']
        self.type = 0
        self.api_options = api_options
        self.page = 1
        super().__init__()

    @discord.ui.button(label="Previous",style=discord.ButtonStyle.gray)
    async def prev_button(self,  interaction:discord.Interaction, button:discord.ui.Button):    
        self.page = max(self.page-1, 1)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next",style=discord.ButtonStyle.gray)
    async def next_button(self,  interaction:discord.Interaction, button:discord.ui.Button):    
        self.page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
 
    @discord.ui.button(label="Type: all",style=discord.ButtonStyle.gray)
    async def toggle_type(self, interaction:discord.Interaction, button:discord.ui.Button):    
        self.type += 1
        if self.type == len(self.types):
            self.type = 0
        self.page = 1
        button.label = f"Type: {self.types[self.type]}"
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    def get_embed(self):
        embed = discord.Embed(title=f"First places")
        content = '```'
        with postgres.instance.managed_session() as session:
            first_places = instance.get_user_1s(
                user_id = self.api_options['user_id'],
                server = self.api_options['server'],
                mode = self.api_options['mode'],
                relax = self.api_options['relax'],
                type = self.types[self.type],
                page = self.page,
                length = 10
            )
            if not first_places or not first_places[1]:
                content += "No scores :/```"
                embed.description = content
                return embed
            embed.title += f" ({first_places[0]})"
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
        await FirstPlacesView({'user_id': user_id, 
                               'server': server,
                               'mode': mode,
                               'relax': relax
                            }).reply(message)