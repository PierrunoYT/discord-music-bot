import asyncio
import discord
import spotipy
import lyricsgenius
import json
import pickle
from pathlib import Path
from queue_manager import QueueManager, QueuedSong
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
    'source_address': '0.0.0.0',
    # Optimize for audio quality
    'preferredcodec': 'opus',
    'preferredquality': '192',
    # Enable fast start
    'buffersize': 32768,
    'audio_buffer_size': 50000
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -af "volume=0.5" -loglevel error -bufsize 32k -maxrate 160k'
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
        self.duration = data.get('duration')
        # Try to extract artist from title (Artist - Title format)
        self.artist = data.get('artist') or (
            data.get('title').split(' - ')[0] if ' - ' in data.get('title', '') 
            else 'Unknown Artist'
        )

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
        self.genius = lyricsgenius.Genius(os.getenv('GENIUS_ACCESS_TOKEN'))
        self.queue_manager = QueueManager()
        self._load_saved_queue()

    def _load_saved_queue(self):
        """Load saved queue state"""
        current_song, queue = self.queue_manager.load_queue()
        if current_song:
            self.bot.loop.create_task(self._restore_current_song(current_song))
        for song in queue:
            self.bot.loop.create_task(self._restore_queued_song(song))

    async def _restore_current_song(self, song):
        """Restore the current song from saved state"""
        try:
            player = await YTDLSource.from_url(song.url, loop=self.bot.loop, stream=True)
            self.current_player = player
        except Exception as e:
            print(f"Error restoring current song: {e}")

    async def _restore_queued_song(self, song):
        """Restore a queued song from saved state"""
        try:
            player = await YTDLSource.from_url(song.url, loop=self.bot.loop, stream=True)
            self.song_queue.append((player, None))
        except Exception as e:
            print(f"Error restoring queued song: {e}")

    def _save_queue_state(self):
        """Save current queue state"""
        current_song = None
        if self.current_player:
            current_song = QueuedSong(
                title=self.current_player.title,
                url=self.current_player.url,
                duration=self.current_player.duration,
                artist=self.current_player.artist
            )
        
        queue = [
            QueuedSong(
                title=player.title,
                url=player.url,
                duration=player.duration,
                artist=player.artist
            )
            for player, _ in self.song_queue
        ]
        
        self.queue_manager.save_queue(current_song, queue)

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
        try:
            if not ctx.message.author.voice:
                await ctx.send("❌ You need to be in a voice channel to use this command!")
                return

            # Check bot permissions
            permissions = ctx.message.author.voice.channel.permissions_for(ctx.guild.me)
            if not permissions.connect or not permissions.speak:
                await ctx.send("❌ I don't have permission to join or speak in that voice channel!")
                return

            # Auto-connect to the user's voice channel
            if ctx.voice_client is None:
                await ctx.message.author.voice.channel.connect()
            elif ctx.voice_client.channel != ctx.message.author.voice.channel:
                await ctx.voice_client.move_to(ctx.message.author.voice.channel)

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
                    self._save_queue_state()
                    await ctx.send(f'Added to queue: {player.title}')
                else:
                    # Play the track immediately
                    player.volume = self.volume
                    ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
                    self.current_player = player
                    self.current_ctx = ctx
                    await ctx.send(f'Now playing: {player.title}')
                
            except Exception as e:
                error_msg = "❌ An error occurred: "
                if "Video unavailable" in str(e):
                    error_msg += "The video is unavailable or region-locked."
                elif "not available in your country" in str(e):
                    error_msg += "This content is not available in your region."
                elif "sign in to confirm your age" in str(e):
                    error_msg += "Age-restricted content cannot be played."
                elif "Private video" in str(e):
                    error_msg += "This video is private."
                else:
                    error_msg += str(e)
                await ctx.send(error_msg)

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stops playback and disconnects the bot"""
        if ctx.voice_client:
            self.song_queue.clear()  # Clear the queue
            self.current_player = None
            self.current_ctx = None
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
        if not ctx.voice_client:
            return
            
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
            self._save_queue_state()
            asyncio.run_coroutine_threadsafe(
                next_ctx.send(f'Now playing: {next_player.title}'),
                self.bot.loop
            )
            
            # If queue loop is enabled, add the song back to the end
            if self.loop_mode == "queue":
                self.song_queue.append((self.current_player, self.current_ctx))
        else:
            # No more songs in queue, disconnect after a delay
            self.current_player = None
            self.current_ctx = None
            asyncio.run_coroutine_threadsafe(
                self._disconnect_after_delay(ctx), 
                self.bot.loop
            )

    @commands.command(name='skip')
    async def skip(self, ctx):
        """Skip the current song"""
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()  # This will trigger play_next via the after callback
            await ctx.send("Skipped the current song")
        else:
            await ctx.send("Nothing is playing right now")

    async def _disconnect_after_delay(self, ctx):
        """Disconnect from voice after a delay if nothing is playing"""
        await asyncio.sleep(180)  # 3 minutes delay
        if ctx.voice_client and not ctx.voice_client.is_playing():
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected due to inactivity")

    @commands.command(name='nowplaying', aliases=['np'])
    async def nowplaying(self, ctx):
        """Display information about the current track"""
        if not self.current_player:
            await ctx.send("No song is currently playing!")
            return

        # Format duration
        duration = self.current_player.duration
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}:{seconds:02d}"

        embed = discord.Embed(title="Now Playing", color=discord.Color.blue())
        embed.add_field(name="Title", value=self.current_player.title, inline=False)
        embed.add_field(name="Artist", value=self.current_player.artist, inline=True)
        embed.add_field(name="Duration", value=duration_str, inline=True)
        embed.add_field(name="URL", value=self.current_player.url, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='queue')
    async def queue(self, ctx):
        """Display the current song queue"""

    @commands.command(name='lyrics')
    async def lyrics(self, ctx):
        """Display lyrics for the currently playing song"""
        if not self.current_player:
            await ctx.send("No song is currently playing!")
            return

        async with ctx.typing():
            try:
                # Extract artist and title from the video title
                title = self.current_player.title
                # Remove common YouTube suffixes
                title = title.replace("(Official Video)", "").replace("(Official Audio)", "")
                title = title.replace("[Official Video]", "").replace("[Official Audio]", "")
                title = title.strip()

                # Try to split artist and song name if they're separated by a dash
                if " - " in title:
                    artist, song = title.split(" - ", 1)
                else:
                    # If no dash, search with full title
                    artist = ""
                    song = title

                # Search for the song
                song = self.genius.search_song(song, artist)
                
                if song:
                    # Split lyrics into chunks if they're too long
                    lyrics = song.lyrics
                    chunks = [lyrics[i:i+2000] for i in range(0, len(lyrics), 2000)]
                    
                    # Send the first message with song info
                    await ctx.send(f"📜 Lyrics for: {song.title} by {song.artist}")
                    
                    # Send lyrics in chunks
                    for chunk in chunks:
                        await ctx.send(f"```{chunk}```")
                else:
                    await ctx.send("Couldn't find lyrics for this song.")
            except Exception as e:
                await ctx.send(f"An error occurred while fetching lyrics: {str(e)}")
        
    @commands.command(name='volume')
    async def volume(self, ctx, volume: int):
        """Change the player volume (0-100)"""
        try:
            if not ctx.voice_client:
                return await ctx.send("❌ Not connected to a voice channel.")
                
            if not 0 <= volume <= 100:
                return await ctx.send("❌ Volume must be between 0 and 100")
                
            # Check if user is in the same voice channel
            if not ctx.author.voice or ctx.author.voice.channel != ctx.voice_client.channel:
                return await ctx.send("❌ You must be in the same voice channel to change the volume.")
                
            self.volume = volume / 100  # Convert to float between 0 and 1
            
            if ctx.voice_client.source:
                ctx.voice_client.source.volume = self.volume
                
            await ctx.send(f"Volume set to {volume}%")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while setting volume: {str(e)}")
        self.volume = volume / 100  # Convert to float between 0 and 1
        
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = self.volume
            
        await ctx.send(f"Volume set to {volume}%")

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
