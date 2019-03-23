from discord.ext import commands
from pathlib import Path
import datetime
import requests
import humanize
import discord
import inspect


RULES_CHANNEL_ID = 554695025485807647
GOV_DOCS_CHANNEL_ID = 553795615042306079


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
            self.log(str(exception), "ERROR")
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

def setup(bot):
    with open(Path('messages/welcome/welcome_message.txt')) as msg_file:
        msg = msg_file.read()
    bot.add_cog(Welcome(bot, welcome_message=msg))
    bot.add_cog(General(bot))
    bot.add_cog(Atlas(bot))