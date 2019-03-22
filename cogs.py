from discord.ext import commands
from pathlib import Path
import requests

RULES_CHANNEL_ID = 554695025485807647

class WelcomeCog(commands.Cog):
    
    def __init__(self, bot, welcome_message):
        self.bot = bot
        self.welcome_message = welcome_message

    @commands.Cog.listener()
    async def on_member_join(self, member):
        rules = member.guild.get_channel(RULES_CHANNEL_ID)
        await member.send(self.welcome_message.format(member=member, guild=member.guild, rules=rules))


class AtlasCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nations(self, ctx):
        response = requests.get('https://mc-atlas.com/nation/api/nation/list').json()
        if response['Status'] == 'OK':
            nations_names = [nation['nationName'] for nation in response['Data']['nationList']]
            await ctx.send('*These are all the nations on Atlas according to our records:' + '\n'.join([
                ' **-** ' + n for n in nations_names]))
        else:
            await ctx.send('*Hmmm, I can\'t seem to find our records at the moment, check back later!')


def setup(bot):
    with open(Path('messages/welcome/welcome_message.txt')) as msg_file:
        msg = msg_file.read()
    bot.add_cog(WelcomeCog(bot, welcome_message=msg))
    bot.add_cog(AtlasCog(bot))