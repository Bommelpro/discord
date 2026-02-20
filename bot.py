import discord
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

active_pings = {}
allowed_roles = {}

def has_permission(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    guild_roles = allowed_roles.get(ctx.guild.id, set())
    if not guild_roles:
        return True
    return any(role.id in guild_roles for role in ctx.author.roles)

@bot.event
async def on_ready():
    print(f'Bot is running as {bot.user}')

@bot.command(name='addpingrole')
@commands.has_permissions(administrator=True)
async def add_role(ctx, role: discord.Role):
    guild_roles = allowed_roles.setdefault(ctx.guild.id, set())
    guild_roles.add(role.id)
    await ctx.send(f'✅ Role **{role.name}** can now use ping commands.')

@bot.command(name='removepingrole')
@commands.has_permissions(administrator=True)
async def remove_role(ctx, role: discord.Role):
    guild_roles = allowed_roles.get(ctx.guild.id, set())
    guild_roles.discard(role.id)
    await ctx.send(f'✅ Role **{role.name}** has been removed.')

@bot.command(name='listpingroles')
async def list_roles(ctx):
    guild_roles = allowed_roles.get(ctx.guild.id, set())
    if not guild_roles:
        await ctx.send('ℹ️ No roles configured – all users have access.')
        return
    names = [ctx.guild.get_role(rid).name for rid in guild_roles if ctx.guild.get_role(rid)]
    await ctx.send(f'✅ Allowed roles: **{", ".join(names)}**')

@bot.command(name='ping')
async def set_ping(ctx, member: discord.Member, interval: int):
    if not has_permission(ctx):
        await ctx.send('❌ You do not have permission to use this command.')
        return
    if interval < 10:
        await ctx.send('❌ Minimum interval is 10 seconds.')
        return

    key = (ctx.guild.id, member.id)

    if key in active_pings:
        active_pings[key].cancel()

    async def ping_loop():
        while True:
            await asyncio.sleep(interval)
            channel = bot.get_channel(ctx.channel.id)
            if channel:
                await channel.send(f'{member.mention} 👋')

    task = asyncio.create_task(ping_loop())
    active_pings[key] = task

    await ctx.send(f'✅ Pinging {member.mention} every **{interval} seconds**.')

@bot.command(name='removeping')
async def remove_ping(ctx, member: discord.Member):
    if not has_permission(ctx):
        await ctx.send('❌ You do not have permission to use this command.')
        return

    key = (ctx.guild.id, member.id)
    if key in active_pings:
        active_pings[key].cancel()
        del active_pings[key]
        await ctx.send(f'✅ Stopped pinging {member.mention}.')
    else:
        await ctx.send(f'❌ No active ping for {member.mention}.')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ You need admin permissions for this command.')
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send('❌ User not found.')
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send('❌ Role not found.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'❌ Missing argument: `{error.param.name}`')

bot.run(os.getenv('TOKEN'))
