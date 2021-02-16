import os
from datetime import datetime
import logging
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv, find_dotenv

# config
load_dotenv(find_dotenv())

TOKEN = os.environ.get("TL_TOKEN")
COMMAND_PREFIX = os.environ.get("TL_COMMAND_PREFIX")
EMOJI_YES = os.environ.get("TL_EMOJI_YES")
EMOJI_MAYBE = os.environ.get("TL_EMOJI_MAYBE")
EMOJI_NO = os.environ.get("TL_EMOJI_NO")

# logging
logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.WARNING)
log = logging.getLogger()
log.setLevel(logging.INFO)
logformat = logging.Formatter('[%(asctime)s] (%(levelname)s) %(message)s')
consolehandler = logging.StreamHandler()
consolehandler.setFormatter(logformat)
log.addHandler(consolehandler)

# init bot
scheduler = AsyncIOScheduler()
scheduler.start()
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
bot.remove_command('help')


# helper functions
async def send_reminder(ctx, time, topic, message_id):
    message = await ctx.fetch_message(message_id)
    ping_list = await get_ping_list(message, ctx.message.guild)
    await ctx.reply(f"it's {time.strftime('%H:%M')}, time for {topic}!\n{ping_list}")


async def get_ping_list(message, guild):
    ping_list = []
    for reaction in message.reactions:
        users = await reaction.users().flatten()
        if reaction.emoji == EMOJI_YES:
            for user in users:
                if user.id != bot.user.id:
                    ping_list.append(guild.get_member(user.id).mention)
        if reaction.emoji == EMOJI_MAYBE:
            for user in users:
                if user.id != bot.user.id:
                    ping_list.append(guild.get_member(user.id).mention)

    # remove duplicates
    ping_list = list(set(ping_list))

    # separate mentions
    ping_list = ' '.join(ping_list)

    return ping_list


async def get_rsvp_list(message, guild):
    rsvp_list = [[], [], []]
    for reaction in message.reactions:
        users = await reaction.users().flatten()
        if str(reaction.emoji) == EMOJI_YES:
            for user in users:
                if user.id != bot.user.id:
                    rsvp_list[0].append(guild.get_member(user.id).display_name)
        if str(reaction.emoji) == EMOJI_MAYBE:
            for user in users:
                if user.id != bot.user.id:
                    rsvp_list[1].append(guild.get_member(user.id).display_name)
        if str(reaction.emoji) == EMOJI_NO:
            for user in users:
                if user.id != bot.user.id:
                    rsvp_list[2].append(guild.get_member(user.id).display_name)

    rsvp_list[0] = ', '.join(rsvp_list[0])
    rsvp_list[1] = ', '.join(rsvp_list[1])
    rsvp_list[2] = ', '.join(rsvp_list[2])

    if not rsvp_list[0]:
        rsvp_list[0] = "-"
    if not rsvp_list[1]:
        rsvp_list[1] = "-"
    if not rsvp_list[2]:
        rsvp_list[2] = "-"

    return rsvp_list


async def update_rsvp_message(message, rsvp_list):
    embed = discord.Embed(description="who's in? <a:eyesshaking:657904205490814996>")
    embed.add_field(name=f"{EMOJI_YES} yes", value=f"{rsvp_list[0]}", inline=False)
    embed.add_field(name=f"{EMOJI_MAYBE} maybe", value=f"{rsvp_list[1]}", inline=False)
    embed.add_field(name=f"{EMOJI_NO} no", value=f"{rsvp_list[2]}", inline=False)

    await message.edit(embed=embed)


# event handlers
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name=f"{bot.command_prefix}help"))
    log.info('logged in as: {0.user} (uid = {0.user.id})'.format(bot))
    log.info('bot ready!')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        log.warning(error)
        await ctx.send("command not found <:peeposadcat:771066963211976774>")
        return
    raise error


@bot.check
async def block_dms(ctx):
    if ctx.guild is not None:
        return True
    await ctx.send("i don't accept direct messages <:9976_smiling_gun:657904189103407105>")
    return False


@bot.event
async def on_raw_reaction_add(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

    # dont trigger on bot reactions
    if payload.user_id == bot.user.id:
        return
    # only trigger on bot messages
    if message.author.id != bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    rsvp_list = await get_rsvp_list(message, guild)
    await update_rsvp_message(message, rsvp_list)


@bot.event
async def on_raw_reaction_remove(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

    # dont trigger on bot reactions
    if payload.user_id == bot.user.id:
        return
    # only trigger on bot messages
    if message.author.id != bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    rsvp_list = await get_rsvp_list(message, guild)
    await update_rsvp_message(message, rsvp_list)


# commands
@bot.command(name='help')
async def help(ctx):
    await ctx.send(
        f"🕒 **Hi, I'm timelord!**\n"
        f"I can help you track attendance for events and remind everyone who voted 'yes' or 'maybe' when it starts.\n\n"
        f"💬 **Commands**\n"
        f"``{COMMAND_PREFIX}add HH:MM event title`` add an event\n"
        f"``{COMMAND_PREFIX}events`` list upcoming events")


@bot.command(name='add')
async def add(ctx, time, *, topic):
    try:
        time = datetime.strptime(time, "%H:%M")
    except:
        await ctx.send("please format your time like this: 19:30")
        return

    today = datetime.today()
    time = time.replace(year=today.year, month=today.month, day=today.day)

    embed = discord.Embed(description="who's in? <a:eyesshaking:657904205490814996>")
    embed.add_field(name=f"{EMOJI_YES} yes", value="-", inline=False)
    embed.add_field(name=f"{EMOJI_MAYBE} maybe", value="-", inline=False)
    embed.add_field(name=f"{EMOJI_NO} no", value="-", inline=False)

    message = await ctx.send(f"**[{time.strftime('%H:%M')}] {topic}**", embed=embed)

    reactions = [EMOJI_YES, EMOJI_MAYBE, EMOJI_NO]
    for reaction in reactions:
        await message.add_reaction(reaction)

    scheduler.add_job(send_reminder, args=[ctx, time, topic, message.id], trigger='date', run_date=time)


@bot.command(name='events')
async def events(ctx):
    job_list = scheduler.get_jobs()
    event_list = ""
    for job in job_list:
        event_name = job.args[2]
        event_time = datetime.strftime(job.next_run_time, "%H:%M")
        event_list += f"**[{event_time}]** {event_name}\n"
    if event_list:
        await ctx.send(f"{event_list}")
    else:
        await ctx.send("there are no upcoming events <:pepehmm:769982318369701898>")


# start bot
log.info("### starting bot ###")
bot.run(TOKEN)
