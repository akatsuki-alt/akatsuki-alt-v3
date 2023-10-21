from typing import List

from discord import Message, Embed
from discordbot.bot import Command, commands
import discord 

class Select(discord.ui.Select):
    def __init__(self, callback_function):
        self.callback_function = callback_function
        options = list()
        for command in commands:
            options.append(discord.SelectOption(label=command.name, description=command.description))
        super().__init__(placeholder="Select an option",max_values=1,min_values=1,options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.callback_function(self.values[0])
    
class SelectView(discord.ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(Select(self.callback_function))

    async def callback_function(self, command_name):
        for command in commands:
            if command.name == command_name:
                await self.message.edit(embed=Embed(title=f"{command.name}", description=f"Aliases: {', '.join(command.triggers)}\n{command.description}\n{command.help}"))
                return
    
    async def reply(self, message: Message):
        content = ""
        for command in commands:
            content += f"{command.name} | {command.description}\n"
        self.message = await message.reply(embed=Embed(title="Help", description=content), view=self)
    
class HelpCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("help", 'show help', ['help', 'h'])
        
    async def run(self, message: Message, arguments: List[str]):
        await SelectView().reply(message)
