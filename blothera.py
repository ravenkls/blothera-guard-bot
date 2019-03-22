from discord.ext import commands
import logging
import os


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    blothera_bot = commands.Bot(command_prefix='b!')
    blothera_bot.load_extension('cogs')
    blothera_bot.run(os.environ.get("TOKEN"))