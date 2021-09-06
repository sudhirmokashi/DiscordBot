import discord
import asyncio
import re

from discord.ext import commands
from utils import permissions,default

class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument :
            try:
                return int(argument, base = 10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid MemberID or Member")
        else:
            return m.id

class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = argument

        if len(ret) > 512:
            reason_max = 512- len(ret) - len(argument)
            raise commands.BadArgument(f"The reason is too long {(len(argument))/(len(reason_max))}")
        return ret

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(kick_members = True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        if await permissions.check_priv(ctx, member):
            return

        try:
            await member.kick(reason = default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("kicked"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(ban_members = True)
    async def ban(self, ctx, member: MemberID, *, reason: str = None):
        m = ctx.guild.get_member(member)
        if await permissions.check_priv(ctx, member):
            return

        try:
            await ctx.guild.ban(discord.Object(id = member), reason = default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("banned"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(1, per = commands.BucketType.user)
    @permissions.has_permissions(ban_members = True)
    async def massban(self, ctx, reason: ActionReason, *, members: MemberID):
        try:
            for member in members:
                await ctx.guild.ban(discord.Object(id = member), reason = default.responsible(ctx.author, reason))
                await ctx.send(defualt.actionmessage("banned"))
            await ctx.send(defualt.actionmessage("massbanned", mass = True))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(ban_members = True)
    async def unban(self, ctx, member: MemberID, *, reason: str = None):
        try:
            await ctx.guild.unban(discord.Object(id = member), reason = default.responsible(ctx.author, reason))
            await ctx.send(defualt.actionmessage("unbanned"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles = True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        if await permissions.check_priv(ctx, member):
            return

        muted_role = next((g for g in ctx.guild.roles if g.name == "Muted"), None)

        if not muted_role:
            return await ctx.send(f"Are you sure you have a role named **Muted**? Remember it is case-sensitive as well")

        try:
            await member.add_roles(muted_role, reason = default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("Muted"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles = True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = None):
        if await permissions.check_priv(ctx, member):
            return

        muted_role = next((g for g in ctx.guild.roles if g.name == "Muted"),None)

        if not muted_role:
            return await ctx.send(f"Are you sure you have a role named **Muted**? Remember it is case-sensitive as well")

        try:
            await member.remove_roles(muted_role, reason = default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("Unmuted"))
        except Exception as e:
            await ctx.send(e)

    @commands.command(aliases = ["ar"])
    @commands.guild_only()
    @permissions.has_permissions(manage_roles = True)
    async def announcerole(self, ctx, *, role: discord.Role):
        if role == ctx.guild.default_role:
            return await ctx.send(f"To prevent mass ping, I cannot allow everyone/here ping")

        if ctx.author.top_role.position <= role.position:
            return await ctx.send(f"It seems that the role you are trying to mention is greater than your role, hence it cannot be mentioned by you.")

        if ctx.me.top_role.position <= role.position:
            return await ctx.send(f"This role is above my permission, hence I cannot mention it.")

        await role.edit(mentionable = True, reason = f"[ {ctx.author} ] announcerole command")
        msg = await ctx.send(f"**{role.name}** is now mentionable. If you dont mention it within 30 seconds, I will revert the changes.")

        while True:
            def role_checker(msg):
                if (role.mention in msg.content):
                    return True
                return False

            try:
                checker = await self.bot.wait_for('message', timeout = 30.0, check = role_checker)
                if checker.author.id == ctx.author.id:
                    return await ctx.send(f"**{role.name}** mentioned by **{ctx.author}** in **{checker.channel.mention}**.")
                    break
                else:
                    await checker.delete()
            except asyncio.TimeoutError:
                await role.edit(mentionable = False, reason = f"[ {ctx.author} ] announcerole command")
                return await ctx.send(f"**{role.name}** was never mentioned by anyone. Reverted the changes.")
                break

    @commands.group()
    @commands.guild_only()
    @permissions.has_permissions(ban_members = True)
    async def find(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @find.command(name = "playing")
    async def find_playing(self, ctx, *, search: str):
        loop = []
        for i in ctx.guild.members:
            if i.activites and (not i.bot):
                for g in i.activities:
                    if g.name and (search.lower() in g.name.lower()):
                        loop.append(f"{i} | {type(g).__name__}: {g.name} ({i.id})")
        await default.prettyResults(ctx, "playing" , f"Found **{len(loop)}** on our search for **{search}**" , loop)

    @find.command(name = "username", aliases = ["uname"])
    async def find_username(self, ctx, *, search: str):
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if (search.lower() in i.name.lower()) and not(i.bot)]
        await default.prettyResults(ctx, "name" , f"Found **{len(loop)}** on your search for **{search}**" , loop)

    @find.command(name = "nickname", aliases = ["nname"])
    async def find_nickname(self, ctx, *, search: str):
        loop = [f"{i.nick} | {i} ({i.id})" for i in ctx.guild.members if i.nick if (search.lower() in i.name.lower()) and not(i.bot)]
        await default.prettyResults(ctx, "name" , f"Found **{len(loop)}** on your search for **{search}**" , loop)

    @find.command(name = "id")
    async def find_id(self, ctx, *, search: str):
        loop = [f"{i} | {i} ({i.id})" for i in ctx.guild.members if (search.lower() in i.name.lower()) and not(i.bot)]
        await default.prettyResults(ctx, "name" , f"Found **{len(loop)}** on your search for **{search}**" , loop)

    @find.command(name = "discriminator", aliases = ["discrim"])
    async def find_discrim(self, ctx, *, search: str):
        if not(len) == 4 or not re.complie("^[0-9]*$").search(search):
            return await ctx.send(f"You must send exactly 4 digits.")

        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await prettyResults(ctx, "discriminator" , f"Found **{len(loop)}** on your search for **{search}**" , loop)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames = True)
    async def nickname(self, ctx, member: discord.Member, *, name: str = None):
        if await permissions.check_priv(ctx, member):
            return

        try:
            await member.edit(nick = name, reason = default.responsible(ctx.author, "Chnaged by command"))
            message = f"Changed **{member.name}**'s nickname to {name}"
            if name is None:
                message = f"Reset **{member.name}**'s name"
            await ctx.send(message)
        except Exception as e:
            await ctx.send(e)

    @commands.group()
    @commands.guild_only()
    @commands.max_concurrency(1, per = commands.BucketType.guild)
    @permissions.has_permissions(manage_messages = True)
    async def erase(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    async def do_removal(self, ctx, limit, predicate, *, before = None, after = None, message = True):
        if limit > 2000:
            return await ctx.send(f"Too many messages ({limit}/2000)")

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id = before)

        if after is not None:
            after = discord.Object(id = after)

        try:
            deleted = await ctx.channel.purge(limit = limit, before = before, after = after, check = predicate)
        except discord.Forbidden:
            await ctx.send(f"I don't have permissions to delete the messages")
        except discord.HTTPException as e:
            return await ctx.send(f"Error: {e} Try a smaller search maybe?")

        deleted = len(deleted)
        if message is True:
            await ctx.send(f'🚮 Successfully removed {deleted} message{"" if deleted == 1 else "s"}.')

    @erase.command()
    async def embeds(self, ctx, search = 100):
        await self.do_removal(ctx, search, lambda e: len(e.embeds))

    @erase.command()
    async def files(self, ctx, search = 100):
        await self.do_removal(ctx, search, lambda e: len(e.attachments))

    @erase.command()
    async def mentions(self, ctx, search = 100):
        await self.do_removal(ctx, search, lambda e: len(e.mentions) or len(role.mentions))

    @erase.command()
    async def images(self, ctx, search = 100):
        await self.do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @erase.command(name = "all")
    async def _remove_all(self, ctx, search = 100):
        await self.do_removal(ctx, search, lambda e: True)

    @erase.command()
    async def user(self, ctx, search = 100):
        await self.do_removal(ctx, search, lambda e: e.author == member)

    @erase.command()
    async def contains(self, ctx, *, substr: str):
        if len(substr) < 3:
            await ctx.send(f"The substring must have at least 3 characters")
        else:
            await self.do_removal(ctx, 100, lambda e: substr in e.content)

    @erase.command(name = "bots")
    async def _bots(self, ctx, search = 100, prefix = None):
        getprefix = prefix if prefix else self.config.prefix
        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or m.content.startswith(tuple(getprefix))
        await self.do_removal(ctx, search, predicate)

    @erase.command(name = "users")
    async def _users(self, ctx, search = 100, prefix = None):
        def predicate(m):
            return m.author.bot is False
        await self.do_removal(ctx, search, predicate)

    @erase.command(name = "emojis")
    async def _emojis(self, ctx, search = 100):
        custom_emoji = re.compile(r'<a?:(<.*?):(\d{17,21})>|[\u263a-\U0001f645]')
        def predicate(m):
            return custom_emoji.search(m.content)
        await self.do_removal(ctx, search, predicate)

    @erase.command(name = "reactions")
    async def _bots(self, ctx, search = 100, prefix = None):
        if search > 2000:
            return await ctx.send(f"Too many messages ({search}/2000)")
        total_reactions = 0
        async for message in ctx.history(limit = search, before = ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()
        await ctx.send(f"Successfully removed {total_reactions} reactions")

def setup(bot):
    bot.add_cog(Moderation(bot))
