# Discord Music Bot

A Discord bot that can play music from YouTube and Spotify in voice channels, with lyrics support via Genius.

## Features

- Play music from YouTube (URLs or search queries)
- Play music from Spotify (track links and playlists)
- Display song lyrics using Genius API
- Basic playback controls (pause, resume, stop)
- Voice channel management (join, leave)
- Queue management and loop modes

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- Discord Bot Token
- Spotify Developer credentials
- Genius API Token

## Installation

1. Clone this repository:
```bash
git clone <your-repository-url>
cd discord-music-bot
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your tokens:
```bash
cp .env.example .env
```

5. Edit the `.env` file with your Discord bot token, Spotify credentials, and Genius token

## Commands

- `!join` - Bot joins your current voice channel
- `!leave` - Bot leaves the voice channel
- `!play <query>` - Play a song or add it to queue (YouTube/Spotify URL or search terms)
- `!pause` - Pause the current song
- `!resume` - Resume playback
- `!stop` - Stop playback and clear the queue
- `!skip` - Skip to the next song in queue
- `!queue` - Display the current queue
- `!volume <0-100>` - Adjust the playback volume
- `!loop [mode]` - Set loop mode (off/track/queue). No argument cycles through modes
- `!lyrics` - Display lyrics for the currently playing song
- `!nowplaying` - Show details about the current song

## Setting Up Development Environment

1. Create a Discord Application and Bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a Spotify Application at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
3. Create a Genius Application at [Genius Developer Portal](https://genius.com/api-clients)
4. Install FFmpeg:
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

## Environment Variables

Create a `.env` file with the following variables:
- `DISCORD_TOKEN`: Your Discord bot token
- `SPOTIFY_CLIENT_ID`: Your Spotify client ID
- `SPOTIFY_CLIENT_SECRET`: Your Spotify client secret
- `GENIUS_ACCESS_TOKEN`: Your Genius API access token

## Features in Detail

### Music Playback
- Support for YouTube videos, playlists, and search queries
- Support for Spotify tracks and playlists
- Automatic queue management
- Volume control
- Multiple loop modes (single track, queue, or off)

### Lyrics Integration
- Automatic lyrics fetching using Genius API
- Smart song title parsing for better lyrics matching
- Support for songs with or without explicit artist information

### Queue Management
- Add songs to queue while playing
- View current queue
- Skip tracks
- Clear queue with stop command
- Persistent queue across bot restarts

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. Copyright (c) 2024 PierrunoYT.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
