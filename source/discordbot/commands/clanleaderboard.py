from typing import List

from discord import Message, Embed, Interaction, ButtonStyle
from discordbot.bot import Command
from utils.parser import parse_args
from discord.ui import View, Button, button
from utils.api.akatsukialt.akataltapi import ClanLeaderboardTypeEnum
from utils.api.akataltapi import instance

class LeaderboardView(View):
    
    def __init__(self, api_options={}):
        self.types = [e.value for e in ClanLeaderboardTypeEnum]
        self.type = 1
        self.page = 1
        self.api_options = api_options
        super().__init__()

    @button(label="Previous", style=ButtonStyle.gray)
    async def prev_button(self, interaction: Interaction, button: Button):    
        self.page = max(self.page-1, 1)
        await interaction.response.defer()
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=self.get_embed(), view=self)

    @button(label="Next",style=ButtonStyle.gray)
    async def next_button(self, interaction: Interaction, button: Button):    
        self.page += 1
        await interaction.response.defer()
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=self.get_embed(), view=self)
    
    @button(label="Sort: 1s", style=ButtonStyle.gray)
    async def toggle_type(self, interaction: Interaction, button: Button):    
        await interaction.response.defer()   
        self.type += 1
        if self.type == len(self.types):
            self.type = 0
        self.page = 1
        button.label = f"Sort: {self.types[self.type]}"
        await interaction.message.edit(embed=self.get_embed(), view=self)
    
    def get_embed(self):
        embed = Embed(title="Leaderboards")
        lb = instance.get_clan_leaderboard(
            server=self.api_options['server'],
            mode=self.api_options['mode'],
            relax=self.api_options['relax'],
            type=self.types[self.type],
            page=self.page,
            length=10
        )
        if not lb or not lb[1]:
            embed.description = "Empty :/"
            return embed
        embed.title += f" ({lb[0]:,})"
        content = "```"
        rank = 10*(self.page-1)
        entry = self.types[self.type]
        
        if entry == "1s":
            entry = "first_places"
        elif entry == "score":
            entry = "ranked_score"
        
        for clan in lb[1]:
            rank+=1
            clan_info = clan.get_clan()
            content += f"#{rank}: {clan_info.name} [{clan_info.tag}] ({clan.__dict__[entry]})\n"
        content += "```"
        embed.description = content
        return embed

    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)

class ClanLeaderboardCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("clanleaderboards", "show clan leaderboards", ["clanlb", "clanleaderboards"])
        
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments, unparsed=True)
        if (link := self.get_link(message)) is None:
            await message.reply("You don't have an account linked!")
            return
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        server = link.default_server
        mode = link.default_mode
        relax = link.default_relax
        if 'server' in parsed:
            if (server := self.get_server(parsed['server'])) is None:
                await message.reply("Unknown server!")
                return
            server = server.server_name
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
        await LeaderboardView({'server': server, 'mode': mode, 'relax': relax}).reply(message)