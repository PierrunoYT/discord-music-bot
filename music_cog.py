import asyncio
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
        self.song_queue = []
        self.volume = 0.5  # Default volume (50%)
        self.loop_mode = "off"  # off, track, queue
        self.current_ctx = None  # Store context for looping

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
    async def play(self, ctx, *, query):
        """Plays audio from YouTube/Spotify URL or searches YouTube for the query"""
        if not ctx.message.author.voice:
            await ctx.send("You need to be in a voice channel to use this command!")
            return

        # Connect to voice channel if not already connected
        if not ctx.voice_client:
            await ctx.message.author.voice.channel.connect()
        
        async with ctx.typing():
            try:
                # Handle different input types
                if 'spotify.com/track' in query:
                    query = await self.get_spotify_track_url(query)
                elif not ('youtube.com' in query or 'youtu.be' in query):
                    # Treat as search query
                    search_query = f"ytsearch:{query}"
                    data = await self.bot.loop.run_in_executor(
                        None, 
                        lambda: ytdl.extract_info(search_query, download=False)
                    )
                    if not data.get('entries'):
                        await ctx.send("No results found.")
                        return
                    query = data['entries'][0]['webpage_url']
                
                # Get the player
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
                
                # If something is playing, add to queue
                if ctx.voice_client.is_playing():
                    self.song_queue.append((player, ctx))
                    await ctx.send(f'Added to queue: {player.title}')
                else:
                    # Play the track immediately
                    player.volume = self.volume
                    ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
                    self.current_player = player
                    self.current_ctx = ctx
                    await ctx.send(f'Now playing: {player.title}')
                
            except Exception as e:
                await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stops playback and disconnects the bot"""
        if ctx.voice_client:
            self.song_queue.clear()  # Clear the queue
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("Stopped playing, cleared queue, and disconnected")
        else:
            await ctx.send("I'm not connected to a voice channel")

    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pauses the currently playing audio"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Playback paused")
        else:
            await ctx.send("Nothing is playing right now")

    @commands.command(name='resume')
    async def resume(self, ctx):
        """Resumes the currently paused audio"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Playback resumed")
        else:
            await ctx.send("Nothing is paused right now")

    def play_next(self, ctx):
        """Play the next song in the queue"""
        if self.loop_mode == "track" and self.current_player:
            # Replay the current track
            player = self.current_player
            ctx = self.current_ctx
            player.volume = self.volume
            ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
            asyncio.run_coroutine_threadsafe(
                ctx.send(f'Looping track: {player.title}'),
                self.bot.loop
            )
        elif self.song_queue:
            next_player, next_ctx = self.song_queue.pop(0)
            next_player.volume = self.volume
            next_ctx.voice_client.play(next_player, after=lambda e: self.play_next(next_ctx))
            self.current_player = next_player
            self.current_ctx = next_ctx
            asyncio.run_coroutine_threadsafe(
                next_ctx.send(f'Now playing: {next_player.title}'),
                self.bot.loop
            )
            
            # If queue loop is enabled, add the song back to the end
            if self.loop_mode == "queue":
                self.song_queue.append((self.current_player, self.current_ctx))

    @commands.command(name='skip')
    async def skip(self, ctx):
        """Skip the current song"""
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()  # This will trigger play_next via the after callback
            await ctx.send("Skipped the current song")
        else:
            await ctx.send("Nothing is playing right now")

    @commands.command(name='queue')
    async def queue(self, ctx):
        """Display the current song queue"""
        
    @commands.command(name='volume')
    async def volume(self, ctx, volume: int):
        """Change the player volume (0-100)"""

    @commands.command(name='loop')
    async def loop(self, ctx, mode: str = None):
        """Set loop mode (off/track/queue)"""
        valid_modes = ['off', 'track', 'queue']
        
        # If no mode specified, cycle through modes
        if mode is None:
            current_index = valid_modes.index(self.loop_mode)
            self.loop_mode = valid_modes[(current_index + 1) % len(valid_modes)]
        elif mode.lower() in valid_modes:
            self.loop_mode = mode.lower()
        else:
            return await ctx.send("Invalid loop mode. Use: off, track, or queue")
            
        await ctx.send(f"Loop mode set to: {self.loop_mode}")
        if not ctx.voice_client:
            return await ctx.send("Not connected to a voice channel.")
            
        if not 0 <= volume <= 100:
            return await ctx.send("Volume must be between 0 and 100")
            
        self.volume = volume / 100  # Convert to float between 0 and 1
        
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = self.volume
            
        await ctx.send(f"Volume set to {volume}%")
        if not self.current_player and not self.song_queue:
            await ctx.send("The queue is empty")
            return

        queue_msg = []
        if self.current_player:
            queue_msg.append(f"Currently playing: {self.current_player.title}")
        
        if self.song_queue:
            queue_msg.append("\nUp next:")
            for i, (player, _) in enumerate(self.song_queue, 1):
                queue_msg.append(f"{i}. {player.title}")
        else:
            queue_msg.append("\nNo songs in queue")

        await ctx.send("\n".join(queue_msg))
