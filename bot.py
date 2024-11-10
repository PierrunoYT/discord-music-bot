import os
from dotenv import load_dotenv

# Load environment variables before any other imports that might use them
load_dotenv()

import discord
from discord.ext import commands
from music_cog import MusicCog

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

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use !help to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ I don't have the required permissions to perform this action.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument provided.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        print(f"Unhandled error: {error}")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
