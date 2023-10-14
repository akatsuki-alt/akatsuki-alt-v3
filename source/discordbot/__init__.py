from discordbot.commands.servers import ServersCommand
from discordbot.commands.ping import PingCommand
from discordbot.commands.link import LinkCommand

import discordbot.bot as bot

bot.commands.append(PingCommand())
bot.commands.append(ServersCommand())
bot.commands.append(LinkCommand())