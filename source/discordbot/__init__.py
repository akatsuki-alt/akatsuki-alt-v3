from discordbot.commands.show import ShowCommand, ResetCommand
from discordbot.commands.setdefault import SetDefaultCommand
from discordbot.commands.servers import ServersCommand
from discordbot.commands.recent import RecentCommand
from discordbot.commands.ping import PingCommand
from discordbot.commands.link import LinkCommand
from discordbot.commands.help import HelpCommand

import discordbot.bot as bot

bot.commands.append(PingCommand())
bot.commands.append(ServersCommand())
bot.commands.append(LinkCommand())
bot.commands.append(SetDefaultCommand())
bot.commands.append(ShowCommand())
bot.commands.append(ResetCommand())
bot.commands.append(HelpCommand())
bot.commands.append(RecentCommand())
