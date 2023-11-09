from discord import Message, Embed, Interaction, ButtonStyle
from utils.api.akatsukialt.akataltapi import UserSortEnum
from discord.ui import View, Button, button
from utils.api.akataltapi import instance
from utils.parser import parse_args
from discordbot.bot import Command
from typing import List

import pycountry

class UsersView(View):
    
    def __init__(self, api_options):
        super().__init__()
        self.types = [e.value for e in UserSortEnum]
        self.type = 0
        self.desc = True
        self.api_options = api_options
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
 
    @button(label="Sort: user_id", style=ButtonStyle.gray)
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

    def get_embed(self):
        embed = Embed(title="Users")
        total, users = instance.get_user_list(
            server = self.api_options['server'],
            page = self.page,
            length=7,
            desc = self.desc,
            sort = self.types[self.type],
            filter = self.api_options['filter']
        )
        content = '```CSS\n'
        if not users:
            content += 'No users :(\n```'
            embed.description = content
            return embed
        for user in users:
            country = pycountry.countries.get(alpha_2=user.country).name.split(",")[0]
            registered_on = user.registered_on.replace("T", " ")
            latest_activity = user.latest_activity.replace("T", " ")
            content += f"{user.username}, {country}, {user.followers} followers\n\tRegistered:  {registered_on}\n\tLast Active: {latest_activity}\n"
        content += '```'
        embed.description = content
        return embed
    
    async def reply(self, message: Message):
        await message.reply(embed=self.get_embed(), view=self)


class UsersCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("users", "list server users", ['users'])
    
    async def run(self, message: Message, arguments: List[str]):
        if (link := self.get_link(message)) is None:
            await message.reply("You don't have an account linked!")
            return
        args = parse_args(arguments)
        server = args['server'] if 'server' in args else link.default_server
        filter = args['filter'] if 'filter' in args else ""
        
        await UsersView({'server': server, 'filter': filter}).reply(message)
