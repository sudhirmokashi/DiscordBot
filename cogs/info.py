import time
import discord
import psutil
import os

from datetime import datetime
from discord.ext import commands
from utils import default

class Information(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.config = default.get("config.json")
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def ping(self, ctx):
        before = time.monotonic()
        before_ws = int(round(self.bot.latency*1000, 1))
        message = await ctx.send("🏓 Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content = f"🏓 WS: {before_ws}ms | REST: {int(ping)}ms")

    @commands.command()
    async def invite(self, ctx):
        await ctx.send(f"**{ctx.author.name}**, use this url to invite me\n<{discord.utils.oauth_url(self.bot.user.id)}>")

    @commands.command(aliases=['info', 'stats', 'status'])
    async def about(self, ctx):
        """ About the bot """
        ramUsage = self.process.memory_full_info().rss / 1024**2
        avgmembers = round(len(self.bot.users) / len(self.bot.guilds))

        embedColour = discord.Embed.Empty
        if hasattr(ctx, 'guild') and ctx.guild is not None:
            embedColour = ctx.me.top_role.colour

        embed = discord.Embed(color=discord.Color(255))
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
#        embed.add_field(name="Last boot", value=default.timeago(datetime.now() - self.bot.uptime()), inline=True)
        embed.add_field(
            name=f"Developer{'' if len(self.config.owners) == 1 else 's'}",
            value=', '.join([str(self.bot.get_user(x)) for x in self.config.owners]),
            inline=True)
        embed.add_field(name="Library", value="discord.py", inline=True)
        embed.add_field(name="Servers", value=f"{len(ctx.bot.guilds)} ( avg: {avgmembers} users/server )", inline=True)
        embed.add_field(name="Commands loaded", value=len([x.name for x in self.bot.commands]), inline=True)
        embed.add_field(name="RAM", value=f"{ramUsage:.2f} MB", inline=True)

        await ctx.send(content=f"ℹ About **{ctx.bot.user}** | **{self.config.version}**", embed=embed)

def setup(bot):
    bot.add_cog(Information(bot))
