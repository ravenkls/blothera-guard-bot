from discord.ext import commands
from pathlib import Path
import requests

RULES_CHANNEL_ID = 554695025485807647
GOV_DOCS_CHANNEL_ID = 553795615042306079

class WelcomeCog(commands.Cog):
    
    def __init__(self, bot, welcome_message):
        self.bot = bot
        self.welcome_message = welcome_message

    @commands.Cog.listener()
    async def on_member_join(self, member):
        rules = member.guild.get_channel(RULES_CHANNEL_ID)
        gov_docs = member.guild.get_channel(GOV_DOCS_CHANNEL_ID)
        await member.send(self.welcome_message.format(member=member, guild=member.guild, rules=rules, gov_docs=gov_docs))


class AtlasCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nations(self, ctx):
        response = requests.get('https://mc-atlas.com/nation/api/nation/list').json()
        if response['Status'] == 'OK':
            nations_names = [nation['nationName'] for nation in response['Data']['nationList']]
            await ctx.send(('*These are all the nations on Atlas according to our records:*\n' + '\n'.join([
                ' **-** ' + n for n in nations_names])[:2000]))
        else:
            await ctx.send('*Hmmm, I can\'t seem to find our records at the moment, check back later!')

    @commands.command()
    async def nation(self, ctx, *, name: str):
        response = requests.get('https://mc-atlas.com/nation/api/nation/list', params={'ShowCitizens': True, 'ShowTowns': True}).json()
        if response['Status'] == 'OK':
            for nation in response['Data']['nationList']:
                if nation['nationName'].lower().strip() == name.lower().strip():
                    owner = ', '.join([p['userName'] for p in nation['citizens'] if p['isLeader']])
                    if not owner:
                        owner = 'N/A'
                    break
            else:
                return await ctx.send(f'I couldn\'t find any nation by the name of {name}')
            string = (f'*Heres what I found on* ***{nation["nationName"]}***\n\n'
                      f'Owner: {owner}\n'
                      f'Number of Towns: {len(nation["towns"])}\n'
                      f'Number of Citizens: {len(nation["citizens"])}')
            await ctx.send(string)

def setup(bot):
    with open(Path('messages/welcome/welcome_message.txt')) as msg_file:
        msg = msg_file.read()
    bot.add_cog(WelcomeCog(bot, welcome_message=msg))
    bot.add_cog(AtlasCog(bot))