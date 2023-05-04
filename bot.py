import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
import os
import datetime
import time
import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

f = open('message_storage.json')
data = json.load(f)
f.close()

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.messages = True

# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)

key_message = None
key_time = None
key_date = None
needs_update = False

YOUR_CHANNEL_ID = 829455356039004163


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    if data['channel_id']:
        key_channel = await bot.fetch_channel(data['channel_id'])
        global key_message
        key_message = await key_channel.fetch_message(data['message_id'])
        global key_time
        key_time = datetime.time(data["hour"], data["minute"])
        global key_date
        key_date = datetime.date(data["year"], data["month"], data["day"])
        Player_Role = discord.utils.get(
            key_channel.guild.roles, name="Playing This Season")
        Playing_Role = discord.utils.get(
            key_channel.guild.roles, name="Is Playing")
        Out_Role = discord.utils.get(
            key_channel.guild.roles, name="Out This Week")
        Nonvoter_Role = discord.utils.get(
            key_channel.guild.roles, name="Hasn't Voted")

        for member in Player_Role.members:
            if not (Playing_Role in member.roles or Out_Role in member.roles or Nonvoter_Role in member.roles):
                await member.add_roles(Nonvoter_Role)

        if not called_on_key_time.is_running():
            called_on_key_time.start()
        if not update_reactions.is_running():
            update_reactions.start()


@bot.command(name='assign_roles')
@commands.has_role('Bot Admin')
async def assign_roles(ctx):
    Player_Role = discord.utils.get(
        ctx.guild.roles, name="Playing This Season")
    Playing_Role = discord.utils.get(ctx.guild.roles, name="Is Playing")
    Out_Role = discord.utils.get(ctx.guild.roles, name="Out This Week")
    Nonvoter_Role = discord.utils.get(ctx.guild.roles, name="Hasn't Voted")

    for member in Player_Role.members:
        if not (Playing_Role in member.roles or Out_Role in member.roles or Nonvoter_Role in member.roles):
            await member.add_roles(Nonvoter_Role)


@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != data["message_id"]:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member == bot.user:
        return
    reaction = str(payload.emoji)

    global needs_update

    if reaction == "✅":
        Role = discord.utils.get(member.guild.roles, name="Is Playing")
        await member.add_roles(Role)
        await key_message.remove_reaction("❎", member)
        Old_Role = discord.utils.get(member.guild.roles, name="Hasn't Voted")
        await member.remove_roles(Old_Role)
        needs_update = True
    elif reaction == "❎":
        Role = discord.utils.get(member.guild.roles, name="Out This Week")
        await member.add_roles(Role)
        await key_message.remove_reaction("✅", member)
        Old_Role = discord.utils.get(member.guild.roles, name="Hasn't Voted")
        await member.remove_roles(Old_Role)
        needs_update = True


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != data["message_id"]:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member == bot.user:
        return
    reaction = str(payload.emoji)

    global needs_update

    if reaction == "✅":
        Other_Role = discord.utils.get(
            member.guild.roles, name="Out This Week")
        if Other_Role not in member.roles:
            New_Role = discord.utils.get(
                member.guild.roles, name="Hasn't Voted")
            await member.add_roles(New_Role)
        Role = discord.utils.get(member.guild.roles, name="Is Playing")
        await member.remove_roles(Role)
        needs_update = True
    elif reaction == "❎":
        Other_Role = discord.utils.get(member.guild.roles, name="Is Playing")
        if Other_Role not in member.roles:
            New_Role = discord.utils.get(
                member.guild.roles, name="Hasn't Voted")
            await member.add_roles(New_Role)
        Role = discord.utils.get(member.guild.roles, name="Out This Week")
        await member.remove_roles(Role)
        needs_update = True


@bot.command(name='openvote')
@commands.has_role('Bot Admin')
async def open_vote(ctx, month: int, day: int, year: int, hour: int):
    called_on_key_time.stop()
    update_reactions.stop()

    Player_Role = discord.utils.get(
        ctx.guild.roles, name="Playing This Season")
    Playing_Role = discord.utils.get(
        ctx.guild.roles, name="Is Playing")
    Out_Role = discord.utils.get(
        ctx.guild.roles, name="Out This Week")
    Nonvoter_Role = discord.utils.get(
        ctx.guild.roles, name="Hasn't Voted")

    for member in Player_Role.members:
        await member.add_roles(Nonvoter_Role)
        await member.remove_roles(Playing_Role, Out_Role)

    date_time = datetime.datetime(year, month, day, hour, 0)
    unix_timestamp = int(time.mktime(date_time.timetuple()))
    sent_message = await ctx.channel.send(f"{Nonvoter_Role.mention} Vote on this message by reacting with ✅ or ❎. Voting ends at <t:{unix_timestamp}:f>, which is <t:{unix_timestamp}:R>.\nIs Playing:\nOut This Week:")
    await sent_message.add_reaction("✅")
    await sent_message.add_reaction("❎")

    data["year"] = year
    data["month"] = month
    data["day"] = day
    data["hour"] = hour
    data["minute"] = 0
    data["message_unix_timestamp"] = unix_timestamp
    data["message_id"] = sent_message.id
    data["channel_id"] = sent_message.channel.id

    global key_time
    key_time = datetime.time(data["hour"], data["minute"])
    global key_date
    key_date = datetime.date(data["year"], data["month"], data["day"])

    global key_message
    key_message = sent_message

    json_object = json.dumps(data, indent=4)
    with open("message_storage.json", "w") as outfile:
        outfile.write(json_object)

    if not called_on_key_time.is_running():
        called_on_key_time.start()
    if not update_reactions.is_running():
        update_reactions.start()


@bot.command(name='closevote')
@commands.has_role('Bot Admin')
async def close_vote(ctx):
    global key_message

    Role = discord.utils.get(key_message.guild.roles, name="Hasn't Voted")
    Playing_Role = discord.utils.get(
        key_message.guild.roles, name="Is Playing")
    Out_Role = discord.utils.get(key_message.guild.roles, name="Out This Week")
    await key_message.edit(content=f"{Role.mention} Vote on this message by reacting with ✅ or ❎. Voting ends at <t:{data['message_unix_timestamp']}:f>, which is <t:{data['message_unix_timestamp']}:R>.\nIs Playing: {', '.join(user.mention for user in Playing_Role.members)}\nOut This Week: {', '.join(user.mention for user in Out_Role.members)}")

    await key_message.channel.send('Voting has closed!')

    data["year"] = 0
    data["month"] = 0
    data["day"] = 0
    data["hour"] = 0
    data["minute"] = 0
    data["message_unix_timestamp"] = 0
    data["message_id"] = 0
    data["channel_id"] = 0

    key_message = None
    global key_time
    key_time = None
    global key_date
    key_date = None
    global needs_update
    needs_update = False

    called_on_key_time.stop()
    update_reactions.stop()

    json_object = json.dumps(data, indent=4)
    with open("message_storage.json", "w") as outfile:
        outfile.write(json_object)


@tasks.loop(hours=1)
async def called_on_key_time():
    if (datetime.date.today() - key_date).days == -1 and datetime.datetime.now().hour == key_time.hour:
        Role = discord.utils.get(key_message.guild.roles, name="Hasn't Voted")
        await key_message.channel.send(f'{Role.mention} This is your 24 hour reminder to please vote by reacting to the vote message!')

@tasks.loop(minutes=1)
async def update_reactions():
    global needs_update
    if not needs_update:
        return
    Role = discord.utils.get(key_message.guild.roles, name="Hasn't Voted")
    Playing_Role = discord.utils.get(
        key_message.guild.roles, name="Is Playing")
    Out_Role = discord.utils.get(key_message.guild.roles, name="Out This Week")
    await key_message.edit(content=f"{Role.mention} Vote on this message by reacting with ✅ or ❎. Voting ends at <t:{data['message_unix_timestamp']}:f>, which is <t:{data['message_unix_timestamp']}:R>.\nIs Playing: {', '.join(user.mention for user in Playing_Role.members)}\nOut This Week: {', '.join(user.mention for user in Out_Role.members)}")

    needs_update = False


@called_on_key_time.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")

bot.run(TOKEN)
