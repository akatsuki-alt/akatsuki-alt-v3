from typing import List

from discord import Message
from discordbot.bot import Command
import utils.postgres as postgres
from utils.database import DBDiscordServer
from utils.api.servers import servers

class SettingsCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("settings", "change settings", ['settings'])
    
    async def run(self, message: Message, arguments: List[str]):
        if len(arguments) < 3:
            await message.reply("Usage: !settings [user/server] [setting] [value]")
            return
        match arguments[0]:
            case "user":
                await message.reply("No user settings available atm.")
                return
            case "server":
                if not message.guild:
                    await message.reply("You can only use this command in a server!")
                    return
                if not message.guild.owner_id == message.author.id:
                    admin = False
                    for role in message.author.roles:
                        if role.name.lower() == "admin":
                            admin = True
                            break
                    if not admin:
                        await message.reply("You need admin role or higher to change server settings!")
                        return
                match arguments[1]:
                    case "prefix":
                        with postgres.instance.managed_session() as session:
                            if (settings := session.get(DBDiscordServer, message.guild.id)) is not None:
                                settings.prefix = arguments[2]
                                session.commit()
                                await message.reply("Command prefix changed.")
                                return
                            else:
                                await message.reply("Something went wrong!")
                                return
                    case "default_server":
                        with postgres.instance.managed_session() as session:
                            if (settings := session.get(DBDiscordServer, message.guild.id)) is not None:
                                for server in servers:
                                    if server.server_name == arguments[2].lower():
                                        settings.default_server = server.server_name
                                        session.commit()
                                        await message.reply("Default server changed.")
                                        return
                                await message.reply("Server not found!")
                                return
                            else:
                                await message.reply("Something went wrong!")
                                return
                    case _:
                        await message.reply("Unknown setting!")
            case _:
                await message.reply("Unknown setting!")