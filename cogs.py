from discord.ext import commands
from pathlib import Path

RULES_CHANNEL_ID = 554695025485807647

class WelcomeCog(commands.Cog):
    
    def __init__(self, bot, welcome_message):
        self.bot = bot
        self.welcome_message = welcome_message

    @commands.Cog.listener()
    async def on_member_join(self, member):
        rules = member.guild.get_channel(RULES_CHANNEL_ID)
        await member.send(self.welcome_message.format(member=member, guild=member.guild, rules=rules))

    
def setup(bot):
    with open(Path('messages/welcome/welcome_message.txt')) as msg_file:
        msg = msg_file.read()
    bot.add_cog(WelcomeCog(bot, welcome_message=msg))