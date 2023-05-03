import discord
from dotenv import load_dotenv
from discord.ext import commands
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN = os.getenv('ADMIN_ID')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!')

YOUR_CHANNEL_ID = 829455356039004163

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if 'happy birthday' in message.content.lower():
        await message.channel.send('Happy Birthday! 🎈🎉')

@client.event
async def on_reaction_add(reaction,user):
    Channel = client.get_channel(YOUR_CHANNEL_ID)
    if reaction.message.channel.id != Channel.id:
        return
    if reaction.emoji == "✅":
        Role = discord.utils.get(user.guild.roles, name="Is Playing")
        await user.add_roles(Role)
        await reaction.message.remove_reaction("❎",user)
        Old_Role = discord.utils.get(user.guild.roles, name="Hasn't Voted")
        await user.remove_roles(Old_Role)
    elif reaction.emoji == "❎":
        Role = discord.utils.get(user.guild.roles, name="Out This Week")
        await user.add_roles(Role)
        await reaction.message.remove_reaction("✅",user)
        Old_Role = discord.utils.get(user.guild.roles, name="Hasn't Voted")
        await user.remove_roles(Old_Role)

@client.event
async def on_reaction_remove(reaction,user):
    Channel = client.get_channel(YOUR_CHANNEL_ID)
    if reaction.message.channel.id != Channel.id:
        return
    if reaction.emoji == "✅":
        New_Role = discord.utils.get(user.guild.roles, name="Hasn't Voted")
        await user.add_roles(New_Role)
        Role = discord.utils.get(user.guild.roles, name="Is Playing")
        await user.remove_roles(Role)
    elif reaction.emoji == "❎":
        New_Role = discord.utils.get(user.guild.roles, name="Hasn't Voted")
        await user.add_roles(New_Role)
        Role = discord.utils.get(user.guild.roles, name="Out This Week")
        await user.remove_roles(Role)

@bot.command(name='openvote')
@commands.has_role('Bot Admin')
async def open_vote(ctx, month: int, day: int, year: int, hour: int, minute: int):
    pass



client.run(TOKEN)
bot.run(TOKEN)