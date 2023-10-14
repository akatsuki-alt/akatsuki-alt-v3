from discordbot.commands.servers import ServersCommand
from discordbot.commands.ping import PingCommand

import discordbot.bot as bot

bot.commands.append(PingCommand())
bot.commands.append(ServersCommand())