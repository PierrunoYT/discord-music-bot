# Discord Music Bot

A Discord bot that can play music from YouTube and Spotify in voice channels.

## Features

- Play music from YouTube (URLs or search queries)
- Play music from Spotify (track links)
- Basic playback controls (pause, resume, stop)
- Voice channel management (join, leave)

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- Discord Bot Token
- Spotify Developer credentials

## Installation

1. Clone this repository:
```bash
git clone <your-repository-url>
cd discord-music-bot
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your tokens:
```bash
cp .env.example .env
```

4. Edit the `.env` file with your Discord bot token and Spotify credentials

## Commands

- `!join` - Bot joins your current voice channel
- `!leave` - Bot leaves the voice channel
- `!play <query>` - Play a song or add it to queue (YouTube URL, search query, or Spotify track link)
- `!pause` - Pause the current song
- `!resume` - Resume playback
- `!stop` - Stop playback and clear the queue
- `!skip` - Skip to the next song in queue
- `!queue` - Display the current queue
- `!volume <0-100>` - Adjust the playback volume

## Setting Up Development Environment

1. Create a Discord Application and Bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a Spotify Application at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
3. Install FFmpeg:
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

## Environment Variables

Create a `.env` file with the following variables:
- `DISCORD_TOKEN`: Your Discord bot token
- `SPOTIFY_CLIENT_ID`: Your Spotify client ID
- `SPOTIFY_CLIENT_SECRET`: Your Spotify client secret

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
