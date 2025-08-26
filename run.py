import nextcord as nc 
import os

from nextcord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = nc.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')




bot.run(TOKEN)