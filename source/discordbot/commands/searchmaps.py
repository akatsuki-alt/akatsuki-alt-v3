from discord import Message, Embed, ButtonStyle, Interaction
from utils.api.akatsukialt.akataltapi import BeatmapSortEnum
from discord.ui import View, button, Button
from utils.api.akataltapi import instance
from utils.parser import parse_args
from discordbot.bot import Command
from typing import List

import discord

class MapsView(View):
    
    def __init__(self, api_options: dict):
        self.api_options = api_options
        self.types = [e.value for e in BeatmapSortEnum]
        self.type = 1
        self.desc = False
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
 
    @button(label="Sort: title", style=ButtonStyle.gray)
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
        links = instance.get_beatmaps(
            sort=self.types[self.type], 
            desc=self.desc,
            beatmap_filter=self.api_options['beatmap_filter'],
            download_link=True
        )
        embed = Embed(title="Download options:", 
                      description="\n".join([f"[{key}]({value})" for (key,value) in links.items()]))
        await interaction.followup.send(embed=embed)

    def get_embed(self) -> Embed:
        embed = Embed(title="Search result")
        beatmaps = instance.get_beatmaps(
            page=self.page, 
            length=7, 
            sort=self.types[self.type], 
            desc=self.desc,
            beatmap_filter=self.api_options['beatmap_filter']
        )
        embed.description = "```"
        if not beatmaps or not beatmaps[1]:
            embed.description += "No beatmaps :(```"
            return embed
        embed.title += f" ({beatmaps[0]:,})"
        for beatmap in beatmaps[1]:
            embed.description += f"{beatmap.stars_nm:.2f}* {beatmap.length / 60:.2f}m | {beatmap.title} [{beatmap.version}]\n"            
        embed.description += "```"
        return embed

    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)

class SearchmapsCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("searchmaps", "search beatmaps", ['searchmaps'])
    
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments)
        beatmap_filter = parsed['beatmap_filter'] if 'beatmap_filter' in parsed else ''
        await MapsView({'beatmap_filter': beatmap_filter}).reply(message)