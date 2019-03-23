from discord.ext import commands
from pathlib import Path
import datetime
import requests
import humanize
import discord


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
    async def nations(self, ctx, *, name: str=''):
        if not name:
            response = requests.get('https://mc-atlas.com/nation/api/nation/list').json()
            if response['Status'] == 'OK':
                nations_names = [nation['nationName'] for nation in response['Data']['nationList']]
                
                embed = discord.Embed(title='Atlas Nation List', colour=0xc62323,
                                    description='\n'.join(['- ' + n for n in nations_names]))

                await ctx.send('*These are all the nations on Atlas according to our records*', embed=embed)
            else:
                await ctx.send('*Hmmm, I can\'t seem to find our records at the moment, check back later!')
        else:
            response = requests.get('https://mc-atlas.com/nation/api/nation/list', params={'ShowCitizens': True, 'ShowTowns': True}).json()
            if response['Status'] == 'OK':
                for nation in response['Data']['nationList']:
                    if nation['nationName'].lower().strip() == name.lower().strip():
                        owners = [p for p in nation['citizens'] if p['isLeader']]
                        owner = {'userName': 'no one', 'userUuid': 'steve'} if not owners else owners[0]
                        break
                else:
                    return await ctx.send(f'I couldn\'t find any nation by the name of {name}')
                

                embed = discord.Embed(title=nation['nationName'], colour=0xc62323,
                                    description=f"The nation {nation['nationName']} is owned by {owner['userName']}")
                embed.set_thumbnail(url="https://minotar.net/avatar/" + owner['userUuid'])
                
                last_seen = sorted(nation['citizens'], key=lambda x: x['userLastSeenTime'], reverse=True)
                last_seen_string = ''
                for player in last_seen[:10]:
                    natural = humanize.naturaltime(datetime.datetime.fromtimestamp(player['userLastSeenTime']/1000))
                    last_seen_string += f'- {player["userName"]} (last seen {natural})\n'
                towns_string = '\n'.join(['- ' + t['townName'] for t in nation['towns']]) or 'N/A'
                last_seen_string = last_seen_string or 'N/A'

                embed.add_field(name="Towns", value=towns_string)
                embed.add_field(name="Citizens", value=last_seen_string, inline=False)

                await ctx.send(content='*Let me just find my notes...*', embed=embed)

def setup(bot):
    with open(Path('messages/welcome/welcome_message.txt')) as msg_file:
        msg = msg_file.read()
    bot.add_cog(WelcomeCog(bot, welcome_message=msg))
    bot.add_cog(AtlasCog(bot))