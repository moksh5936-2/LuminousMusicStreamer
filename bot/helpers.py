"""
Helper functions and command handlers for the bot.
"""
import logging
import re
from pyrogram import filters
from pyrogram.types import Message
from bot.ytdl import get_video_info

logger = logging.getLogger(__name__)

# Command regex patterns
PLAY_COMMAND = filters.command(["play", "p"])
STOP_COMMAND = filters.command(["stop", "s"])
SKIP_COMMAND = filters.command(["skip", "next", "n"])
PAUSE_COMMAND = filters.command(["pause"])
RESUME_COMMAND = filters.command(["resume", "r"])
QUEUE_COMMAND = filters.command(["queue", "q"])
LYRICS_COMMAND = filters.command(["lyrics", "ly"])
VOLUME_COMMAND = filters.command(["volume", "vol", "v"])

def register_handlers(client):
    """
    Register message handlers for the bot commands
    
    Args:
        client (pyrogram.Client): The Pyrogram client
    """
    @client.on_message(PLAY_COMMAND)
    async def play_handler(_, message: Message):
        """Handle /play command"""
        try:
            # Check if there's a query after the command
            if len(message.command) < 2:
                await message.reply("Please provide a song name or YouTube URL.\nExample: `/play despacito`")
                return
                
            # Get the query (everything after the command)
            query = " ".join(message.command[1:])
            
            # Send a processing message
            processing_msg = await message.reply(f"🔍 Searching for: `{query}`...")
            
            # Get video info (but don't download)
            info = await get_video_info(query)
            
            if info:
                title, duration, thumbnail, video_url = info
                response = f"""
✅ **Found Video**

🎵 **Title:** {title}
⏱ **Duration:** {duration}
🔗 **Watch on YouTube:** [Click here]({video_url})

_To actually play this in a voice chat, I would need PyTgCalls which is not currently compatible with this environment. If you'd like to deploy a full version with voice chat support, please check the project repository._
"""
                await processing_msg.edit(response, disable_web_page_preview=False)
            else:
                await processing_msg.edit("❌ Could not find or process the requested video.")
                
        except Exception as e:
            logger.error(f"Error in play_handler: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
    
    @client.on_message(STOP_COMMAND)
    async def stop_handler(_, message: Message):
        """Handle /stop command"""
        await message.reply("⚠️ Voice chat streaming is not available in this simplified version.")
    
    @client.on_message(SKIP_COMMAND)
    async def skip_handler(_, message: Message):
        """Handle /skip command"""
        await message.reply("⏭️ Skip functionality is not available in this simplified version.")
    
    @client.on_message(PAUSE_COMMAND)
    async def pause_handler(_, message: Message):
        """Handle /pause command"""
        await message.reply("⏸️ Pause functionality is not available in this simplified version.")
    
    @client.on_message(RESUME_COMMAND)
    async def resume_handler(_, message: Message):
        """Handle /resume command"""
        await message.reply("▶️ Resume functionality is not available in this simplified version.")
    
    @client.on_message(QUEUE_COMMAND)
    async def queue_handler(_, message: Message):
        """Handle /queue command"""
        await message.reply("📋 Queue is empty. Playback functionality is not available in this simplified version.")
    
    @client.on_message(LYRICS_COMMAND)
    async def lyrics_handler(_, message: Message):
        """Handle /lyrics command"""
        if len(message.command) < 2:
            await message.reply("Please provide a song name to search for lyrics.\nExample: `/lyrics despacito`")
            return
            
        query = " ".join(message.command[1:])
        await message.reply(f"🎵 Lyrics for '{query}' would appear here in the full version.")
    
    @client.on_message(VOLUME_COMMAND)
    async def volume_handler(_, message: Message):
        """Handle /volume command"""
        if len(message.command) < 2:
            await message.reply("Please provide a volume level (1-100).\nExample: `/volume 50`")
            return
            
        try:
            volume_level = int(message.command[1])
            if 0 <= volume_level <= 100:
                await message.reply(f"🔊 Volume set to {volume_level}% (This is a demo response, volume control is not available in this simplified version)")
            else:
                await message.reply("⚠️ Volume level must be between 0 and 100")
        except ValueError:
            await message.reply("⚠️ Please provide a valid number for volume level")
    
    # Add help command handler
    @client.on_message(filters.command(["help", "h"]))
    async def help_handler(_, message: Message):
        """Handle /help command"""
        help_text = """
**🎵 LuminousMusicBot Commands 🎵**

**Core Commands:**
`/play <song_name or URL>` - Search for a song and play it
`/stop` - Stop playback and leave voice chat
`/skip` or `/next` - Skip to the next song in queue
`/pause` - Pause the current playback
`/resume` - Resume paused playback

**Additional Commands:**
`/queue` or `/q` - Show the current song queue
`/volume <level>` or `/vol <level>` - Set volume (0-100)
`/lyrics <song_name>` or `/ly <song_name>` - Get lyrics for a song

**General Commands:**
`/start` - Start the bot
`/help` - Show this help message
`/about` - Information about this bot

**Note:** This is a simplified version without voice chat functionality.
For a full version with voice chat support, you would need to deploy with PyTgCalls.
"""
        await message.reply(help_text)
    
    # Add start command handler
    @client.on_message(filters.command("start"))
    async def start_handler(_, message: Message):
        """Handle /start command"""
        start_text = f"""
**👋 Hello {message.from_user.mention}!**

I'm **LuminousMusicBot**, a lightweight Telegram bot for YouTube search and info.

Use `/help` to see available commands.
"""
        await message.reply(start_text)
        
    # Add about command handler
    @client.on_message(filters.command("about"))
    async def about_handler(_, message: Message):
        """Handle /about command"""
        about_text = """
**🎵 LuminousMusicBot**

A lightweight Telegram bot designed for music playback in voice chats.

**Technologies:**
- Pyrogram (Telegram API)
- YT-DLP (YouTube integration)
- Flask (Web Interface)
- SQLAlchemy (Database)

**Made by:** Moksh Gupta

**Note:** This is a simplified version for demonstration.
"""
        await message.reply(about_text)

    logger.info("Command handlers registered")
