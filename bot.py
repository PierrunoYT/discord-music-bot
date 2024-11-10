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

# Remove default help command to create our own
bot.remove_command('help')

@bot.command(name='help')
async def help(ctx):
    """Shows all available commands"""
    embed = discord.Embed(
        title="Music Bot Commands",
        description="Here are all available commands:",
        color=discord.Color.blue()
    )

    # Music commands
    music_commands = {
        "play <query/URL>": "Play a song from YouTube/Spotify or search query",
        "pause": "Pause the current song",
        "resume": "Resume playback",
        "stop": "Stop playback and clear queue",
        "skip": "Skip to the next song",
        "queue": "Show the current song queue",
        "nowplaying (np)": "Show details about the current song",
        "volume <0-100>": "Adjust the playback volume",
        "loop [mode]": "Set loop mode (off/track/queue)",
        "lyrics": "Show lyrics for the current song"
    }

    # Add fields for each command
    for cmd, desc in music_commands.items():
        embed.add_field(
            name=f"!{cmd}",
            value=desc,
            inline=False
        )

    # Add footer with prefix information
    embed.set_footer(text="Use ! before each command")

    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')
    await bot.add_cog(MusicCog(bot))

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
