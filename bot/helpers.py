"""
Helper functions and command handlers for the bot.
"""
import logging
import re
from pyrogram import filters
from pyrogram.types import Message
from bot.ytdl import get_video_info
from bot.music_player import MusicPlayer

# Set up logging
logger = logging.getLogger(__name__)

# Global music player instance to be initialized when needed
music_player = None

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
    # Initialize the music player
    global music_player
    music_player = MusicPlayer(client, None)  # No session string needed
    
    @client.on_message(PLAY_COMMAND)
    async def play_handler(_, message: Message):
        """Handle /play command"""
        try:
            # Check if this is a private chat (where voice chats aren't available)
            if message.chat.type == "private":
                await message.reply("""
❌ **I can't play music in private chats!**

Voice chats are only available in groups and channels.

Please add me to a group as an administrator, then use the /play command there.

See /help for setup instructions.
""")
                return
                
            # Check if there's a query after the command
            if len(message.command) < 2:
                await message.reply("Please provide a song name or YouTube URL.\nExample: `/play despacito`")
                return
                
            # Get the query (everything after the command)
            query = " ".join(message.command[1:])
            
            # Send a processing message
            processing_msg = await message.reply(f"🔍 Searching for: `{query}`...")
            
            # Get chat ID
            chat_id = message.chat.id
            
            # Try to play the song in the voice chat
            result = await music_player.play(chat_id, query, message)
            
            # Update the processing message with the result
            await processing_msg.edit(result)
                
        except Exception as e:
            logger.error(f"Error in play_handler: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
    
    # Helper function to check if chat is private
    async def check_private_chat(message):
        if message.chat.type == "private":
            await message.reply("""
❌ **Music commands only work in groups!**

Voice chats are only available in groups and channels.

Please add me to a group as an administrator, then use commands there.

See /help for setup instructions.
""")
            return True
        return False
            
    @client.on_message(STOP_COMMAND)
    async def stop_handler(_, message: Message):
        """Handle /stop command"""
        try:
            # Check if this is a private chat
            if await check_private_chat(message):
                return
                
            chat_id = message.chat.id
            result = await music_player.stop(chat_id)
            await message.reply(result)
        except Exception as e:
            logger.error(f"Error in stop_handler: {e}")
            await message.reply(f"❌ Error stopping playback: {str(e)}")
    
    @client.on_message(SKIP_COMMAND)
    async def skip_handler(_, message: Message):
        """Handle /skip command"""
        try:
            # Check if this is a private chat
            if await check_private_chat(message):
                return
                
            chat_id = message.chat.id
            if hasattr(music_player, 'skip'):
                result = await music_player.skip(chat_id)
                await message.reply(result)
            else:
                await message.reply("⏭️ Skip functionality is not available in this version.")
        except Exception as e:
            logger.error(f"Error in skip_handler: {e}")
            await message.reply(f"❌ Error skipping: {str(e)}")
    
    @client.on_message(PAUSE_COMMAND)
    async def pause_handler(_, message: Message):
        """Handle /pause command"""
        try:
            # Check if this is a private chat
            if await check_private_chat(message):
                return
                
            chat_id = message.chat.id
            if hasattr(music_player, 'pause'):
                result = await music_player.pause(chat_id)
                await message.reply(result)
            else:
                await message.reply("⏸️ Pause functionality is not available in this version.")
        except Exception as e:
            logger.error(f"Error in pause_handler: {e}")
            await message.reply(f"❌ Error pausing: {str(e)}")
    
    @client.on_message(RESUME_COMMAND)
    async def resume_handler(_, message: Message):
        """Handle /resume command"""
        try:
            # Check if this is a private chat
            if await check_private_chat(message):
                return
                
            chat_id = message.chat.id
            if hasattr(music_player, 'resume'):
                result = await music_player.resume(chat_id)
                await message.reply(result)
            else:
                await message.reply("▶️ Resume functionality is not available in this version.")
        except Exception as e:
            logger.error(f"Error in resume_handler: {e}")
            await message.reply(f"❌ Error resuming: {str(e)}")
    
    @client.on_message(QUEUE_COMMAND)
    async def queue_handler(_, message: Message):
        """Handle /queue command"""
        try:
            # Check if this is a private chat
            if await check_private_chat(message):
                return
                
            chat_id = message.chat.id
            if hasattr(music_player, 'queue'):
                result = await music_player.queue(chat_id)
                await message.reply(result)
            else:
                await message.reply("📋 Queue functionality is not available in this version.")
        except Exception as e:
            logger.error(f"Error in queue_handler: {e}")
            await message.reply(f"❌ Error getting queue: {str(e)}")
    
    @client.on_message(LYRICS_COMMAND)
    async def lyrics_handler(_, message: Message):
        """Handle /lyrics command"""
        # This command can work in any chat since it doesn't rely on voice chats
        if len(message.command) < 2:
            await message.reply("Please provide a song name to search for lyrics.\nExample: `/lyrics despacito`")
            return
            
        query = " ".join(message.command[1:])
        await message.reply(f"🎵 Lyrics for '{query}' would appear here in the full version.")
    
    @client.on_message(VOLUME_COMMAND)
    async def volume_handler(_, message: Message):
        """Handle /volume command"""
        try:
            # Check if this is a private chat
            if await check_private_chat(message):
                return
                
            if len(message.command) < 2:
                await message.reply("Please provide a volume level (1-100).\nExample: `/volume 50`")
                return
                
            try:
                volume_level = int(message.command[1])
                if 0 <= volume_level <= 100:
                    chat_id = message.chat.id
                    if hasattr(music_player, 'volume'):
                        result = await music_player.volume(chat_id, volume_level)
                        await message.reply(result)
                    else:
                        await message.reply(f"🔊 Volume set to {volume_level}% (This is a demo response, volume control is not available in this version)")
                else:
                    await message.reply("⚠️ Volume level must be between 0 and 100")
            except ValueError:
                await message.reply("⚠️ Please provide a valid number for volume level")
        except Exception as e:
            logger.error(f"Error in volume_handler: {e}")
            await message.reply(f"❌ Error setting volume: {str(e)}")
    
    # Add help command handler
    @client.on_message(filters.command(["help", "h"]))
    async def help_handler(_, message: Message):
        """Handle /help command"""
        help_text = """
**🎵 LuminousMusicBot Commands 🎵**

**Core Commands:**
`/play <song_name or URL>` - Search for a song and play it in voice chat
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

**⚠️ IMPORTANT SETUP INSTRUCTIONS ⚠️**
1. Add this bot to your group as an **administrator**
2. Give the bot **"Manage Voice Chats"** permission
3. Start a voice chat in your group
4. Use /play command in the group (not in private chat)

**Note:** Voice chats are only available in **groups** and **channels**, not in private chats.
For best performance, ensure the bot has permission to join and speak in voice chats.
"""
        await message.reply(help_text)
    
    # Add start command handler
    @client.on_message(filters.command("start"))
    async def start_handler(_, message: Message):
        """Handle /start command"""
        start_text = f"""
**👋 Hello {message.from_user.mention}!**

I'm **LuminousMusicBot**, a lightweight Telegram music bot that can play songs in voice chats.

**Key Features:**
• Play music from YouTube in voice chats
• Queue system for multiple songs
• Control playback with pause/resume/skip commands
• Web interface for song search history

**⚠️ IMPORTANT: I can only play music in group voice chats! ⚠️**
1. Add me to your group as an administrator
2. Give me "Manage Voice Chats" permission
3. Start a voice chat in your group
4. Use /play command in the group

Use `/help` to see all available commands.
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
