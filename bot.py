import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from music_cog import MusicCog

# Load environment variables
load_dotenv()

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')
    await bot.add_cog(MusicCog(bot))

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
