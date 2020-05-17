from discord.ext import commands
from MainCog import MainCog
import os

TOKEN = os.environ['DISCORD_TOKEN']

bot = commands.Bot(command_prefix='!gundam ')
bot.add_cog(MainCog(bot))
bot.run(TOKEN)