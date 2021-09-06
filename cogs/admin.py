import aiohttp
import time
import discord
import importlib
import os
import sys

from discord.ext import commands
from utils import permissions, default, http, dataIO

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")
        self._last_result = None

    @commands.command()
    async def amiadmin(self, ctx):
        if ctx.author.id in self.config.owners:
            return await ctx.send(f"Yes **{ctx.author.name}**, you are an admin! ✅ ")
        if ctx.author.id == 86477779717066752:
            return await ctx.send(f"Well as you are the developer for this bot's source code, you are an admin by default! ✅✅✅✅ ")
        await ctx.send(f"Nope. You are not an admin.")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def load(self, ctx, name: str):
        try:
            self.bot.load_extension(f"{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Loaded Extension {name}.py")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def unload(self, ctx, name: str):
        try:
            self.bot.unload_extension(f"{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Unloaded Extension {name}.py")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reload(self, ctx, name: str):
        try:
            self.bot.reload_extension(f"{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Reloaded Extensions {name}.py")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reloadall(self, ctx):
        output = ""
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"{name}")
                except Exception as e:
                    error_collection.append([file, default.traceback_maker(e, advance = False)])

        if error_collection == []:
            await ctx.send(f"Successfully reloaded all extensions")
        else:
            otuput = "\n".join([f"**g[0]**```diff\n-{g[1]}```" for g in error_collection])
            return await ctx.send(
            f"Attempted to reload all extensions, was able to reload, "
            f"however the follwing failed..\n\n{output}"
            )

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reloadutils(self, ctx, name: str):
        name_maker = f"utils/{name}.py"
        try:
            module_name = importlib.import_module(f"utils.{name}")
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await ctx.send(f"No module named **{name_maker}**")
        except Exception as e:
            error = default.traceback_maker(e)
            return await ctx.send(f"Module **{name_maker}** returned error and was not reloaded...\n{error}")
        await ctx.send(f"Reloaded Module **{name_maker}**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def shutdown(self, ctx):
        await ctx.send(f"Shutting down...")
        time.sleep(1)
        sys.exit(0)

    @commands.command()
    @commands.check(permissions.is_owner)
    async def dm(self, ctx, member: discord.Member = None, *, message: str):
        """ DM the user of your choice """
        #user = self.bot.get_user(user_id)
        if member is None:
            return await ctx.send(f"Could not find any UserID matching **{member}**")

        try:
            await member.send(member, message)
            await ctx.send(f"✉️ Sent a DM to **{user_id}**")
        except :
            await ctx.send("This user might be having DMs blocked or it's a bot account...")

    @commands.group()
    @commands.check(permissions.is_owner)
    async def change(self ,ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="playing")
    @commands.check(permissions.is_owner)
    async def change_playing(self, ctx, *, playing: str):
        """ Change playing status. """
        if self.config.status_type == "idle":
            status_type = discord.Status.idle
        elif self.config.status_type == "dnd":
            status_type = discord.Status.dnd
        else:
            status_type = discord.Status.online

        if self.config.activity_type == "listening":
            playing_type = 2
        elif self.config.activity_type == "watching":
            playing_type = 3
        else:
            playing_type = 0

        try:
            await self.bot.change_presence(
                activity=discord.Activity(type=playing_type, name=playing),
                status=status_type
            )
            dataIO.change_value("config.json", "playing", playing)
            await ctx.send(f"Successfully changed playing status to **{playing}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name = "username")
    @commands.check(permissions.is_owner)
    async def change_username(self, ctx, *, name: str = None):
        try:
            await self.bot.user.edit(username = name)
            await ctx.send(f"Successfully changed username to **{name}**")
        except discord.HTTPException as err:
            await ctx.send(err)

    @change.command(name = "nickname")
    @commands.check(permissions.is_owner)
    async def change_nickname(self, ctx, *, name: str = None):
        try:
            await ctx.guild.me.edit(nick = name)
            if name:
                await ctx.send(f"Successfully changed nickname to **{name}**")
            else:
                await ctx.send(f"Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)

    @change.command(name="avatar")
    @commands.check(permissions.is_owner)
    async def change_avatar(self, ctx, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip('<>') if url else None

        try:
            bio = await http.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            await ctx.send(f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            await ctx.send("This URL does not contain a useable image")
        except discord.HTTPException as err:
            await ctx.send(err)
        except TypeError:
            await ctx.send("You need to either provide an image URL or upload one with the command")

def setup(bot):
    bot.add_cog(Admin(bot))
