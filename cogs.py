from discord.ext import commands
from pathlib import Path
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import style
from io import BytesIO
from mcstatus import MinecraftServer
import datetime
import requests
import humanize
import discord
import inspect
import os


RULES_CHANNEL_ID = 554695025485807647
GOV_DOCS_CHANNEL_ID = 553795615042306079
LORD_ROLE_ID = 553616009572122625
MY_ID = 206079414709125120
ATLAS_USER = os.environ.get('ATLAS_USER')
ATLAS_PASS = os.environ.get('ATLAS_PASS')
BLOTHERA_KINGDOM_ID = 277


style.use('dark_background')


async def is_lord(ctx):
    if ctx.guild.id == 553615313045028865:
        if ctx.author.top_role >= ctx.guild.get_role(LORD_ROLE_ID):
            return True
    return ctx.author.id == MY_ID




class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")
    
    def get_usage(self, command):
        args_spec = inspect.getfullargspec(command.callback)  # Get arguments of command
        args_info = []
        [args_info.append("".join(["<", arg, ">"])) for arg in args_spec.args[2:]]  # List arguments
        if args_spec.defaults is not None:
            for index, default in enumerate(args_spec.defaults):  # Modify <> to [] for optional arguments
                default_arg = list(args_info[-(index + 1)])
                default_arg[0] = "["
                default_arg[-1] = "]"
                args_info[-(index + 1)] = "".join(default_arg)
        if args_spec.varargs:  # Compensate for *args
            args_info.append("<" + args_spec.varargs + ">")
        if args_spec.kwonlyargs:
            args_info.extend(["<" + a + ">" for a in args_spec.kwonlyargs])
        args_info.insert(0, self.bot.command_prefix + command.name)  # Add command name to the front
        return " ".join(args_info)  # Return args

        args = inspect.getfullargspec(command.callback)
        args_info = {}
        for arg in args[0][2:] + args[4]:
            if arg not in args[6]:
                args_info[arg] = None
            else:
                args_info[arg] = args[6][arg].__name__
        usage = " ".join("<{}: {}>".format(k, v) if v is not None else "<{}>".format(k) for k, v in args_info.items())
        return " ".join([command.name, usage])

    @commands.command(aliases=["h"])
    async def help(self, ctx, cmd=None):
        """Shows you a list of commands"""
        if cmd is None:
            help_embed = discord.Embed(title="Commands are listed below", colour=0xc62323)
            help_embed.__setattr__("description", "Type `{}help <command>` for more information".format(self.bot.command_prefix))
            help_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png', static_format='png'))
            help_embed.set_thumbnail(url=self.bot.user.avatar_url_as(format='png', static_format='png'))
            for cog_name, cog in self.bot.cogs.items():
                cmds = cog.get_commands()
                if cmds:
                    help_embed.add_field(name=cog_name, value="\n".join("`{0.name}`".format(c) for c in cmds if not c.hidden))
            await ctx.author.send(embed=help_embed)
            await ctx.message.add_reaction("\U0001F4EC")
        else:
            command = self.bot.get_command(cmd)
            if command is None:
                ctx.send("That command does not exist")
            else:
                help_embed = discord.Embed(title=command.name, colour=0xc62323)
                desc = command.description
                help_embed.description = desc if desc != "" else command.callback.__doc__
                aliases = ", ".join("`{}`".format(c) for c in command.aliases)
                if len(aliases) > 0:
                    help_embed.add_field(name="Aliases", value=aliases)
                usage = self.get_usage(command)
                help_embed.add_field(name="Usage", value="`" + usage + "`")
                await ctx.send(embed=help_embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, plugin):
        """Reloads all plugins or a specific plugin"""
        self.bot.reload_extension(plugin)

    @commands.command(name="eval", hidden=True)
    @commands.is_owner()
    async def _eval(self, ctx, *, code):
        """Evaluates Python code"""
        try:
            if code.startswith("await "):
                response = await eval(code.replace("await ", ""))
            else:
                response = eval(code)
            if response is not None:
                await ctx.send("```python\n{}```".format(response))
        except Exception as e:
            await ctx.send("```python\n{}```".format(e))

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exception):
        if type(exception) == discord.ext.commands.errors.CommandNotFound:
            return
        error_embed = discord.Embed(colour=0xFF0000)
        if type(exception) == discord.ext.commands.errors.MissingRequiredArgument:
            arg = str(exception).split()[0]
            error_embed.title = "Syntax Error"
            error_embed.description = "Usage: `{}`".format(self.get_usage(ctx.command))
            error_embed.set_footer(text="{} is a required argument".format(arg))
        elif type(exception) == discord.ext.commands.errors.BadArgument:
            error_embed.title = "Syntax Error"
            error_embed.description = "Usage: `{}`".format(self.get_usage(ctx.command))
            error_embed.set_footer(text=str(exception))
        else:
            error_embed.title = "Error"
            error_embed.description = "`" + str(exception) + "`"
        if error_embed.description is not None:
            return await ctx.send(embed=error_embed)

    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Activity(name='the Kingdom', type=discord.ActivityType.watching)
        await self.bot.change_presence(activity=game)


class Welcome(commands.Cog):
    
    def __init__(self, bot, welcome_message):
        self.bot = bot
        self.welcome_message = welcome_message

    @commands.Cog.listener()
    async def on_member_join(self, member):
        rules = member.guild.get_channel(RULES_CHANNEL_ID)
        gov_docs = member.guild.get_channel(GOV_DOCS_CHANNEL_ID)
        await member.send(self.welcome_message.format(member=member, guild=member.guild, rules=rules, gov_docs=gov_docs))


class Atlas(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nations(self, ctx, *, name: str=''):
        """Gets information on the nations of Atlas"""
        if not name:
            response = requests.get('https://mc-atlas.com/nation/api/nation/list').json()
            if response['Status'] == 'OK':
                nations_names = [nation['nationName'] for nation in response['Data']['nationList'] if not nation.get('nationIsAdmin')]
                
                embed = discord.Embed(title='Atlas Nation List', colour=0xc62323,
                                    description='\n'.join(['- ' + n for n in nations_names]))

                await ctx.send('*These are all the nations on Atlas according to our records*', embed=embed)
            else:
                await ctx.send('*Hmmm, I can\'t seem to find our records at the moment, check back later!')
        else:
            response = requests.get('https://mc-atlas.com/nation/api/nation/list', params={'ShowCitizens': True, 'ShowTowns': True}).json()
            if response['Status'] == 'OK':
                for nation in filter(lambda x: not x.get('nationIsAdmin'), response['Data']['nationList']):
                    if nation['nationName'].lower().strip() == name.lower().strip():
                        try:
                            owners = [p for p in nation['citizens'] if p.get('isLeader')]
                            owners = [{'userName': 'no one', 'userUuid': 'steve'}] if not owners else owners
                        except KeyError as e:
                            return await ctx.send('*I can\'t seem to find our records at the moment, please check back later*')
                        break
                else:
                    return await ctx.send(f'I couldn\'t find any nation by the name of {name}')
                

                embed = discord.Embed(title=nation['nationName'], colour=0xc62323,
                                    description=f"The nation {nation['nationName']} is owned by {', '.join([x['userName'] for x in owners])}")
                embed.set_thumbnail(url="https://minotar.net/avatar/" + owners[0]['userUuid'])
                
                last_seen = sorted(nation['citizens'], key=lambda x: x['userLastSeenTime'], reverse=True)
                last_seen = sorted(last_seen, key=lambda x: x['userLastSeenTime'] == 0, reverse=True)
                last_seen_string = ''
                for player in last_seen[:10]:
                    if player['userLastSeenTime'] != 0:
                        natural = humanize.naturaltime(datetime.datetime.fromtimestamp(int(str(player['userLastSeenTime'])[:10])))
                        last_seen_string += f'- {player["userName"]} (last seen {natural})\n'
                    else:
                        last_seen_string += f'- {player["userName"]} (ONLINE)\n'
                towns_string = '\n'.join(['- ' + t['townName'] for t in nation['towns']]) or 'N/A'
                last_seen_string = last_seen_string or 'N/A'

                embed.add_field(name="Towns", value=towns_string)
                embed.add_field(name="Citizens", value=last_seen_string, inline=False)

                await ctx.send(content='*Let me just find my notes...*', embed=embed)

    @commands.command()
    async def leaderboard(self, ctx, *, category='top nation'):
        """Retrieves the Atlas leaderboard"""
        loading_message = await ctx.send(f'Searching for `{category.title()}` leaderboard...')
        leaderboard_urls = ['Overall', 'Military', 'Industry', 'Technology', 'Culture', 'Misc']
        leaderboard = None
        for url in leaderboard_urls:
            response = requests.get('https://www.mc-atlas.com/leaderboards/' + url)
            soup = BeautifulSoup(response.text, 'lxml')
            if category.lower() == 'top' or category.lower() == 'top nation':
                leaderboard = soup.findAll('div', class_='large-leaderboard')
            elif url == 'Overall':
                leaderboard = [x for x in soup.findAll('div', class_='leaderboard-mini') if x.select_one('h1').text.lower() == category.lower()]
            else:
                leaderboard = [x for x in soup.findAll('div', class_='normal-leaderboard') if x.select_one('h1').text.lower() == category.lower()]
            if leaderboard:
                leaderboard = leaderboard[0]
                break
        else:
            return await ctx.send('*I couldn\'t find any leaderboards by that category...\n'
                                  'Go to https://www.mc-atlas.com/leaderboards/Overall to view the leaderboard names*')
            leaderboard = leaderboard[0]
        nations_lis = leaderboard.findAll('li')
        nations = [(n.select_one('mark').text, n.select_one('small').text) for n in nations_lis if n.select_one('mark').text != '-']

        embed = discord.Embed(description='\n'.join(f'**{i}.** {n[0]} - {n[1]}' for i, n in enumerate(nations, start=1)), colour=0xEAEE57)
        embed.set_author(name=leaderboard.select_one('h1').text, icon_url='https://www.mc-atlas.com' + leaderboard.select_one('img')['src'])
        await loading_message.edit(content='*This is the current leaderboard according to our records...*', embed=embed)

    async def atlas_login(self):
        session = requests.Session()
        login_page = session.get('https://mc-atlas.com/user/login')
        soup = BeautifulSoup(login_page.text, 'lxml')

        form_build_id = soup.select_one('input[name=form_build_id]')['value']
        form_id = soup.select_one('input[name=form_id]')['value']
        op = soup.select_one('input[name=op]')['value']

        data = {'name': ATLAS_USER,
                'pass': ATLAS_PASS,
                'form_build_id': form_build_id,
                'form_id': form_id,
                'op': op}

        login_request = session.post('https://mc-atlas.com/user/login', data=data,
                                     allow_redirects=False)
        
        return session

    async def get_town_info(self, town_name, session=None):
        if not session:
            session = await self.atlas_login()
        towns = session.get('https://www.mc-atlas.com/nation/v2/api/currentusernation').json()['Data']['nation']['towns']
        try:
            town = [t for t in towns if t['townName'].lower() == town_name.lower()][0]
        except IndexError:
            return None
        town_id = town['townId']
        town_response = session.get('https://www.mc-atlas.com/nation/v2/api/towninfo', params={'TownId': town_id}).json()
        return town_response['Data']

    async def get_coffers_log(self):
        session = await self.atlas_login()

        params = {'MinTime': 0, 'NationId': BLOTHERA_KINGDOM_ID}
        coffers = session.get('https://mc-atlas.com/nation/v2/api/getcofferlog', params=params).json()
        history = coffers['Data']['CofferHistory']
        nice_logs = []
        char_count = 0
        for n, log in enumerate(history):
            if 'Player' in log['Description']:
                dt = datetime.datetime.fromtimestamp(int(str(log['Timestamp'])[:10])).strftime('%d/%m/%y')
                player = log["Metadata"]["PlayerName"]
                total = log["NationCoffers"]
                delta = abs(int(total) - int(history[n+1]['NationCoffers']))
                if log['Description'] == 'Player Deposit':
                    nice_logs.append(f'**{dt} >** {player} added {delta} to the coffers ({total})')
                    char_count += len(f'**{dt} >** {player} added {delta} to the coffers ({total})')
                elif log['Description'] == 'Player Withdraw':
                    nice_logs.append(f'**{dt} >** {player} removed {delta} from the coffers ({total})')
                    char_count += len(f'**{dt} >** {player} removed {delta} from the coffers ({total})')
            if char_count > 1850:
                print(char_count)
                nice_logs.pop(-1)
                break
        
        return '**Blothera Coffers (Players Only)**\n' + '\n'.join(nice_logs)


    async def get_coffers_graph(self):
        session = await self.atlas_login()
        
        params = {'MinTime': 0, 'NationId': BLOTHERA_KINGDOM_ID}
        coffers = session.get('https://mc-atlas.com/nation/v2/api/getcofferlog', params=params).json()

        history = coffers['Data']['CofferHistory']
        coffer_logs = [h['NationCoffers'] for h in history]
        date_logs = [datetime.datetime.fromtimestamp(int(str(h['Timestamp'])[:10])) for h in history]

        fig = plt.figure()

        ax = fig.add_subplot(111)

        ax.set_title('Kingdom of Blothera Coffers')
        ax.set_xlabel('Date')
        ax.set_ylabel('Coffers')
        ax.plot(date_logs, coffer_logs, label='Coffers')

        loc = mdates.AutoDateLocator()
        loc.intervald[mdates.HOURLY] = [24]
        ax.xaxis.set_major_locator(loc)
        fmter = mdates.DateFormatter('%d/%m/%Y')
        ax.xaxis.set_major_formatter(fmter)

        image = BytesIO()
        fig.savefig(image, format='png', transparent=True)
        image.seek(0)
        return coffer_logs[0], image

    @commands.command()
    @commands.check(is_lord)
    async def blothera(self, ctx, *, request):
        """Retrieves information on Blothera (Lords only)"""
        if request.lower() == 'coffers':
            amount, coffer_graph = await self.get_coffers_graph()
            await ctx.send(content=f'*The nation\'s coffers currently stands at {amount:,}*', file=discord.File(coffer_graph, filename='blothera_coffers.png'))
        elif request.lower() == 'playerlogs':
            logs = await self.get_coffers_log()
            await ctx.send(logs)
        elif request.split()[0].lower() == 'town':
            try:
                town_name = request[4:].lower().strip()
            except IndexError:
                await ctx.send('Please enter the town name')
            else:
                session = await self.atlas_login()
                town_info = await self.get_town_info(town_name, session=session)
            
                embed = discord.Embed(title=town_info['townName'], colour=0xc62323)
                map_file = BytesIO(session.get('https://www.mc-atlas.com/nation/v2'+town_info['map']['url'][1:]).content)
                await ctx.send(content='**'+town_info['townName']+'**', file=discord.File(map_file, filename='town.png'))
            

def setup(bot):
    with open(Path('messages/welcome/welcome_message.txt')) as msg_file:
        msg = msg_file.read()
    bot.add_cog(Welcome(bot, welcome_message=msg))
    bot.add_cog(General(bot))
    bot.add_cog(Atlas(bot))