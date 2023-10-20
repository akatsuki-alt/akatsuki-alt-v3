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
    async def prev_button(self,button:discord.ui.Button,interaction:discord.Interaction):    
        self.page = max(self.page-1, 1)
        await interaction.message.edit(embed=self.get_embed())

    @discord.ui.button(label="Next",style=discord.ButtonStyle.gray)
    async def next_button(self,button:discord.ui.Button,interaction:discord.Interaction):    
        self.page += 1
        await interaction.message.edit(embed=self.get_embed())
        
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
        rank = 1*(self.page-1)
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
        await LeaderboardView({'mode': mode, 'relax': relax, 'server': server, 'type': type}).reply(message)