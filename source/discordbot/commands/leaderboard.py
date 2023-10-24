from utils.api.akatsukialt.akataltapi import UserExtraLeaderboardTypeEnum
from utils.api.akataltapi import instance
from utils.parser import parse_args
from discordbot.bot import Command
from discord import Message, Embed
from typing import List, Optional
from discord.ui import View, button
import discord

class LeaderboardView(View):
    
    def __init__(self, api_options={}):
        self.page = 1
        self.api_options = api_options
        super().__init__()
    
    @discord.ui.button(label="Previous",style=discord.ButtonStyle.gray)
    async def prev_button(self, interaction:discord.Interaction, button:discord.ui.Button):    
        self.page = max(self.page-1, 1)
        await interaction.response.defer()
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next",style=discord.ButtonStyle.gray)
    async def next_button(self, interaction:discord.Interaction, button:discord.ui.Button):    
        self.page += 1
        await interaction.response.defer()
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=self.get_embed(), view=self)
        
    def get_embed(self):
        embed = Embed(title="Leaderboards")
        lb = instance.get_user_extra_leaderboard(
            server=self.api_options['server'],
            mode=self.api_options['mode'],
            relax=self.api_options['relax'],
            page=self.page,
            length=10,
            type=self.api_options['type']
        )
        if not lb:
            embed.description = "Empty :/"
            return embed
        content = "```"
        rank = 10*(self.page-1)
        entry = "first_places"
        for enum in UserExtraLeaderboardTypeEnum:
            if enum.value == self.api_options['type']:
                entry = enum.name
                break
        for user in lb:
            rank+=1
            user_info = instance.get_user_info(user.user_id, user.server)
            username = 'API error'
            if user_info:
                username = user_info.username
            content += f"#{rank}: {username} ({user.__dict__[entry]})\n"
        content += "```"
        embed.description = content
        return embed

    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)

class ShowLeaderboardCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("leaderboards", "show leaderboards", ['showlb','leaderboards', 'lb'], "!leaderboards (server=server)")
    
    
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments, unparsed=True)
        if (link := self.get_link(message)) is None:
            await message.reply(f"You don't have an account linked!")
            return
        modes = {'std': (0,0), 'std_rx': (0,1), 'std_ap': (0,2), 'taiko': (1,0), 'taiko_rx': (1,1), 'ctb': (2,0), 'ctb_rx': (2,1), 'mania': (3,0)}
        mode = link.default_mode
        relax = link.default_relax
        server = link.default_server
        type = '1s'
        if 'server' in parsed:
            if (server := self.get_server(parsed['server'])) is None:
                await message.reply(f"Server not found!")
                return
            server = server.server_name
        if 'type' in parsed:
            values = [e.value for e in UserExtraLeaderboardTypeEnum]
            if parsed['type'] not in values:
                await message.reply(f"Invalid type! valid types: {', '.join(values)}")
                return
            type = parsed['type']
        if parsed['unparsed']:
            if parsed['unparsed'][0] not in modes:
                await message.reply(f"Invalid mode! Valid modes: {','.join(modes.keys())}")
                return
            mode, relax = modes[parsed['unparsed'][0]]
        await LeaderboardView({'mode': mode, 'relax': relax, 'server': server, 'type': type}).reply(message)