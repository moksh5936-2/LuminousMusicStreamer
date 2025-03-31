# LuminousMusicBot

A lightweight Telegram music bot that streams YouTube audio in voice chats with multi-group support.

Made by Moksh Gupta

## Features

- High-quality audio streaming in Telegram voice chats
- Web interface for searching and managing music
- YouTube search with thumbnail previews
- Multi-group support with independent playback
- Search history tracking
- Optimized for Replit and Heroku deployment

## Bot Commands

### Core Commands
- `/play <song>` or `/p <song>` - Play a song in the voice chat
- `/stop` or `/s` - Stop playback and leave the voice chat
- `/skip` or `/next` - Skip to the next song in queue
- `/pause` - Pause the current playback
- `/resume` or `/r` - Resume paused playback

### Additional Commands
- `/queue` or `/q` - Show the current song queue
- `/volume <level>` or `/vol <level>` - Set volume (0-100)
- `/lyrics <song>` or `/ly <song>` - Get lyrics for a song

### General Commands
- `/start` - Start the bot
- `/help` or `/h` - Display help message with all commands
- `/about` - Information about this bot

## Deploy to Heroku

Just click the button below to deploy to Heroku:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

After deployment:
1. Go to the Heroku Dashboard > Your App > Resources
2. Enable both dynos: "web" and "worker"
3. Go to Settings > Reveal Config Vars to ensure all environment variables are set

## Manual Deployment

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` file from `.env.example` and fill in your credentials
4. Run the web interface: `gunicorn --bind 0.0.0.0:$PORT main:app`
5. Run the Telegram bot: `python main.py`

## Environment Variables

- `API_ID`: Telegram API ID from my.telegram.org/apps
- `API_HASH`: Telegram API Hash from my.telegram.org/apps
- `BOT_TOKEN`: Telegram Bot Token from @BotFather
- `SESSION_SECRET`: Random secret key for Flask sessions
- `SESSION_STRING`: Pyrogram session string (optional)
- `DATABASE_URL`: Database URL for SQLAlchemy