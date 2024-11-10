import discord
import spotipy
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
import youtube_dl
import os

# YouTube DL options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Initialize Spotify client
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
))

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_player = None

    async def get_spotify_track_url(self, spotify_url):
        """Convert Spotify URL to YouTube search query"""
        try:
            track = spotify.track(spotify_url)
            search_query = f"{track['artists'][0]['name']} - {track['name']}"
            data = await self.bot.loop.run_in_executor(
                None, 
                lambda: ytdl.extract_info(f"ytsearch:{search_query}", download=False)
            )
            return data['entries'][0]['webpage_url']
        except Exception as e:
            raise Exception(f"Error processing Spotify link: {str(e)}")

    @commands.command(name='play')
    async def play(self, ctx, *, url):
        """Plays audio from YouTube or Spotify"""
        if not ctx.message.author.voice:
            await ctx.send("You need to be in a voice channel to use this command!")
            return

        # Connect to voice channel if not already connected
        if not ctx.voice_client:
            await ctx.message.author.voice.channel.connect()
        
        async with ctx.typing():
            try:
                # Convert Spotify URL to YouTube URL if necessary
                if 'spotify.com/track' in url:
                    url = await self.get_spotify_track_url(url)
                
                # Get the player
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                
                # Stop current playback if any
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                
                # Play the new track
                ctx.voice_client.play(player)
                self.current_player = player
                await ctx.send(f'Now playing: {player.title}')
                
            except Exception as e:
                await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stops playback and disconnects the bot"""
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("Stopped playing and disconnected")
        else:
            await ctx.send("I'm not connected to a voice channel")
