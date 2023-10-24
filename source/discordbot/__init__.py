from discordbot.commands.show import ShowCommand, ResetCommand
from discordbot.commands.setdefault import SetDefaultCommand
from discordbot.commands.servers import ServersCommand
from discordbot.commands.recent import RecentCommand
from discordbot.commands.ping import PingCommand
from discordbot.commands.link import LinkCommand
from discordbot.commands.help import HelpCommand
from discordbot.commands.leaderboard import ShowLeaderboardCommand
from discordbot.commands.show1s import Show1sCommand
from discordbot.commands.showclears import ShowClearsCommand
from discordbot.commands.addqueue import AddQueueCommand
import discordbot.bot as bot

bot.commands.append(PingCommand())
bot.commands.append(ServersCommand())
bot.commands.append(LinkCommand())
bot.commands.append(SetDefaultCommand())
bot.commands.append(ShowCommand())
bot.commands.append(ResetCommand())
bot.commands.append(HelpCommand())
bot.commands.append(RecentCommand())
bot.commands.append(ShowLeaderboardCommand())
bot.commands.append(Show1sCommand())
bot.commands.append(ShowClearsCommand())
bot.commands.append(AddQueueCommand())