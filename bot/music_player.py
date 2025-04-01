"""
Music player module that handles voice chat streaming with PyTgCalls
"""
import logging
import asyncio
import os
import time
import random
import tempfile
import pathlib
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, Update, StreamEnded, AudioQuality
from pyrogram import Client
from pyrogram.errors import ChannelInvalid, PeerIdInvalid, UserNotParticipant
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.phone import CreateGroupCall, DiscardGroupCall
from pyrogram.raw.types import InputPeerChannel, InputChannel
from bot.ytdl import download_and_extract_audio, get_video_info

logger = logging.getLogger(__name__)

class MusicPlayer:
    """
    Music player class to handle voice chat streaming in multiple groups
    """
    def __init__(self, client: Client, session_string=None):
        """
        Initialize the music player
        
        Args:
            client (pyrogram.Client): Pyrogram client
            session_string (str, optional): Pyrogram session string for PyTgCalls
        """
        # Store Pyrogram client
        self.client = client
        
        # Initialize PyTgCalls client
        self.pytgcalls = PyTgCalls(client)
        
        # Dictionary to track active streams by chat_id
        self.active_chats = {}
        
        # Dictionary to store queued songs
        self.queue = {}
        
        # Start PyTgCalls
        try:
            self.pytgcalls.start()
            logger.info("PyTgCalls successfully started")
        except Exception as e:
            logger.error(f"Failed to start PyTgCalls: {e}")
            raise
        
        # Set up update handler for PyTgCalls v2.1.1
        @self.pytgcalls.on_update()
        async def on_update(_, update: Update):
            # Check if the update is a stream end event
            if isinstance(update, StreamEnded) and update.stream_type == StreamEnded.Type.AUDIO:
                chat_id = update.chat_id
                logger.info(f"Stream ended in chat {chat_id}")
                
                # Play next song in queue if available
                if chat_id in self.queue and self.queue[chat_id]:
                    # Get next song from queue
                    next_song = self.queue[chat_id].pop(0)
                    logger.info(f"Playing next song from queue: {next_song['title']}")
                    
                    # Update current playing info
                    self.active_chats[chat_id] = next_song
                    
                    # Play the next song
                    try:
                        audio_file = next_song.get('file_path')
                        if audio_file and os.path.exists(audio_file):
                            await self.pytgcalls.change_stream(
                                chat_id,
                                MediaStream(
                                    audio_file,
                                    audio_parameters=AudioQuality.HIGH
                                )
                            )
                            logger.info(f"Changed stream to next song in chat {chat_id}")
                        else:
                            logger.error(f"Audio file not found for next song in queue")
                            if chat_id in self.active_chats:
                                self.active_chats.pop(chat_id)
                    except Exception as e:
                        logger.error(f"Error changing stream: {e}")
                        if chat_id in self.active_chats:
                            self.active_chats.pop(chat_id)
                else:
                    # No more songs in queue, clean up
                    logger.info(f"No more songs in queue for chat {chat_id}, leaving voice chat")
                    try:
                        await self.pytgcalls.leave_call(chat_id)
                    except Exception as e:
                        logger.error(f"Error leaving call: {e}")
                    
                    # Remove from active chats
                    if chat_id in self.active_chats:
                        self.active_chats.pop(chat_id)
        
        logger.info("Music player initialized with PyTgCalls")
    
    async def _ensure_voice_chat(self, chat_id: int):
        """
        Ensure that a voice chat is active in the group
        
        Args:
            chat_id (int): The chat ID
            
        Returns:
            bool: True if voice chat is active or was created, False otherwise
        """
        try:
            # Check if the chat_id is a valid group or channel ID (not a private chat)
            # Valid group IDs are usually negative numbers, but not all negative numbers are groups
            # We need to make sure it's a super group or channel
            
            if chat_id > 0:
                logger.error(f"Cannot create voice chat in private chat {chat_id}")
                return False
                
            # Try to get group call info
            try:
                peer = await self.client.resolve_peer(chat_id)
            except Exception as e:
                logger.error(f"Failed to resolve peer for chat_id {chat_id}: {e}")
                return False
                
            # Check if this is a channel/supergroup
            if isinstance(peer, InputPeerChannel):
                try:
                    full_chat = await self.client.invoke(
                        GetFullChannel(
                            channel=InputChannel(
                                channel_id=peer.channel_id,
                                access_hash=peer.access_hash
                            )
                        )
                    )
                    
                    # Check if there's already a group call
                    if hasattr(full_chat, 'full_chat') and hasattr(full_chat.full_chat, 'call'):
                        logger.info(f"Voice chat is already active in chat {chat_id}")
                        return True
                    
                    # If not, try to create one
                    logger.info(f"Creating voice chat in chat {chat_id}")
                    try:
                        await self.client.invoke(
                            CreateGroupCall(
                                peer=peer,
                                random_id=random.randint(10000, 999999999)
                            )
                        )
                        logger.info(f"Voice chat created in chat {chat_id}")
                        # Sleep briefly to allow voice chat to initialize
                        await asyncio.sleep(2)
                        return True
                    except Exception as e:
                        if "USER_NOT_ADMIN" in str(e):
                            logger.error(f"Bot is not an admin in the chat {chat_id}, cannot create voice chat")
                            return False
                        elif "PARTICIPANTS_TOO_FEW" in str(e):
                            logger.error(f"Not enough participants to create a voice chat in {chat_id}")
                            return False
                        else:
                            logger.error(f"Failed to create voice chat: {e}")
                            return False
                except Exception as e:
                    logger.error(f"Error getting full channel info: {e}")
                    return False
            else:
                logger.error(f"Chat ID {chat_id} is not a channel/group (peer type: {type(peer).__name__})")
                return False
        except Exception as e:
            logger.error(f"Error ensuring voice chat: {e}")
            return False
    
    async def play(self, chat_id: int, query: str, message):
        """
        Play audio in a voice chat
        
        Args:
            chat_id (int): Chat ID where to play the audio
            query (str): YouTube search query or URL
            message (Message): Original message that triggered the command
            
        Returns:
            str: Status message
        """
        try:
            # Check if this is a valid group chat first
            if chat_id > 0:
                return "❌ Voice chats are only available in groups and channels, not in private chats."
            
            # Get video info first
            logger.info(f"Searching for query: {query}")
            video_info = await get_video_info(query)
            
            if not video_info:
                return "❌ Could not find the requested song."
                
            title, duration, thumbnail, video_url = video_info
            
            # Check if we're already playing something in this chat
            if chat_id in self.active_chats:
                # Add to queue instead
                if chat_id not in self.queue:
                    self.queue[chat_id] = []
                
                # Add to queue
                queue_item = {
                    'title': title,
                    'duration': duration,
                    'video_url': video_url,
                    'thumbnail': thumbnail,
                    'query': query
                }
                
                self.queue[chat_id].append(queue_item)
                queue_position = len(self.queue[chat_id])
                
                logger.info(f"Added to queue at position {queue_position} in chat {chat_id}: {title}")
                
                return f"""
✅ **Added to Queue**

🎵 **Title:** {title}
⏱ **Duration:** {duration}
🔗 **Watch on YouTube:** [Click here]({video_url})

📊 **Position in queue:** {queue_position}
"""
            
            # Try to download the audio
            try:
                # First, ensure there's a voice chat
                voice_chat_active = await self._ensure_voice_chat(chat_id)
                if not voice_chat_active:
                    return """❌ Could not join or create a voice chat.

Possible reasons:
• The bot isn't an administrator in the group
• The bot doesn't have permission to manage voice chats
• There isn't an active voice chat and the bot can't create one
• The chat is not a group or channel

Please make sure:
1. The bot is added as an administrator
2. The bot has 'Manage Voice Chats' permission
3. You're using the bot in a group or channel, not a private chat
4. A voice chat is already active if the bot can't create one"""
                
                # Download the audio
                logger.info(f"Downloading audio for: {title}")
                audio_info = await download_and_extract_audio(query)
                
                if not audio_info or not audio_info[0]:
                    return "❌ Failed to download audio."
                
                audio_file, _, _, _ = audio_info
                
                # Join the voice chat and play the audio (PyTgCalls v2.1.1)
                try:
                    await self.pytgcalls.play(
                        chat_id,
                        MediaStream(
                            audio_file,
                            audio_parameters=AudioQuality.HIGH
                        )
                    )
                    
                    # Save info for the active chat
                    self.active_chats[chat_id] = {
                        'title': title,
                        'duration': duration,
                        'video_url': video_url,
                        'thumbnail': thumbnail,
                        'file_path': audio_file,
                        'query': query
                    }
                    
                    logger.info(f"Now playing in chat {chat_id}: {title}")
                    
                    return f"""
✅ **Now Playing**

🎵 **Title:** {title}
⏱ **Duration:** {duration}
🔗 **Watch on YouTube:** [Click here]({video_url})

📱 **Status:** Playing in voice chat
"""
                except Exception as e:
                    # Handle specific errors with better messages
                    if "No active group call" in str(e):
                        return "❌ No active voice chat found. Please start a voice chat first."
                    elif "GROUPCALL_FORBIDDEN" in str(e):
                        return "❌ The bot doesn't have permission to join the voice chat. Make sure it's an admin with 'Manage Voice Chats' permission."
                    elif "GROUPCALL_INVALID" in str(e):
                        return "❌ The voice chat is no longer active or valid. Try starting a new voice chat."
                    else:
                        logger.error(f"Error joining voice chat: {e}")
                        return f"❌ Error joining voice chat: {str(e)}"
                    
            except Exception as e:
                logger.error(f"Error downloading audio: {e}")
                return f"❌ Error downloading audio: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in play function: {e}")
            return f"❌ An error occurred: {str(e)}"
    
    async def stop(self, chat_id: int):
        """
        Stop playing and leave the voice chat
        
        Args:
            chat_id (int): Chat ID where to stop playing
            
        Returns:
            str: Status message
        """
        try:
            if chat_id in self.active_chats:
                # Get the song details
                song_info = self.active_chats[chat_id]
                title = song_info.get('title', 'Unknown')
                
                # Stop streaming and leave voice chat (PyTgCalls v2.1.1)
                try:
                    await self.pytgcalls.leave_call(chat_id)
                    logger.info(f"Left voice chat in {chat_id}")
                except Exception as e:
                    logger.error(f"Error leaving voice chat: {e}")
                
                # Clean up
                self.active_chats.pop(chat_id, None)
                
                # Clear queue
                if chat_id in self.queue:
                    self.queue.pop(chat_id, None)
                
                return f"🛑 Stopped playing **{title}** and left the voice chat."
            else:
                return "❌ I'm not playing anything in this chat."
                
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return f"❌ Error stopping playback: {str(e)}"
            
    async def skip(self, chat_id: int):
        """
        Skip to the next song in queue
        
        Args:
            chat_id (int): Chat ID where to skip
            
        Returns:
            str: Status message
        """
        try:
            # Check if there's an active stream
            if chat_id not in self.active_chats:
                return "❌ No active playback to skip."
                
            current_song = self.active_chats[chat_id]['title']
            
            # Check if there are songs in queue
            if chat_id not in self.queue or not self.queue[chat_id]:
                # No songs in queue, just stop (PyTgCalls v2.1.1)
                try:
                    await self.pytgcalls.leave_call(chat_id)
                    self.active_chats.pop(chat_id, None)
                    return f"⏭ Skipped **{current_song}**. No more songs in queue."
                except Exception as e:
                    logger.error(f"Error leaving voice chat: {e}")
                    return f"❌ Error skipping: {str(e)}"
            
            # Get next song from queue
            next_song = self.queue[chat_id].pop(0)
            next_title = next_song['title']
            
            # Try to download the next audio if needed
            if 'file_path' not in next_song or not os.path.exists(next_song['file_path']):
                try:
                    audio_info = await download_and_extract_audio(next_song['query'])
                    if audio_info and audio_info[0]:
                        next_song['file_path'] = audio_info[0]
                    else:
                        return "❌ Failed to download next audio."
                except Exception as e:
                    logger.error(f"Error downloading next audio: {e}")
                    return f"❌ Error downloading next audio: {str(e)}"
            
            # Change stream (PyTgCalls v2.1.1)
            try:
                await self.pytgcalls.change_stream(
                    chat_id,
                    MediaStream(
                        next_song['file_path'],
                        audio_parameters=AudioQuality.HIGH
                    )
                )
                
                # Update current playing info
                self.active_chats[chat_id] = next_song
                
                return f"""
⏭ Skipped to next song

🎵 **Now Playing:** {next_title}
⏱ **Duration:** {next_song['duration']}
🔗 **Watch on YouTube:** [Click here]({next_song['video_url']})
"""
            except Exception as e:
                logger.error(f"Error changing stream: {e}")
                return f"❌ Error skipping: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in skip function: {e}")
            return f"❌ Error skipping: {str(e)}"
            
    async def pause(self, chat_id: int):
        """
        Pause the current playback
        
        Args:
            chat_id (int): Chat ID where to pause
            
        Returns:
            str: Status message
        """
        try:
            if chat_id not in self.active_chats:
                return "❌ No active playback to pause."
                
            try:
                await self.pytgcalls.pause(chat_id)
                return "⏸ Music playback paused."
            except Exception as e:
                logger.error(f"Error pausing stream: {e}")
                return f"❌ Error pausing: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in pause function: {e}")
            return f"❌ Error pausing: {str(e)}"
            
    async def resume(self, chat_id: int):
        """
        Resume paused playback
        
        Args:
            chat_id (int): Chat ID where to resume
            
        Returns:
            str: Status message
        """
        try:
            if chat_id not in self.active_chats:
                return "❌ No paused playback to resume."
                
            try:
                await self.pytgcalls.resume(chat_id)
                return "▶️ Music playback resumed."
            except Exception as e:
                logger.error(f"Error resuming stream: {e}")
                return f"❌ Error resuming: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in resume function: {e}")
            return f"❌ Error resuming: {str(e)}"
            
    async def queue(self, chat_id: int):
        """
        Get the current queue
        
        Args:
            chat_id (int): Chat ID to get queue for
            
        Returns:
            str: Queue information
        """
        try:
            # Check if there's an active stream
            if chat_id not in self.active_chats:
                return "❌ No active playback or queue."
                
            current_song = self.active_chats[chat_id]['title']
            
            # Check if there are songs in queue
            if chat_id not in self.queue or not self.queue[chat_id]:
                return f"""
📋 **Queue Information**

🎵 **Now Playing:** {current_song}

No more songs in queue.
"""
            
            # Construct queue message
            queue_msg = f"📋 **Queue Information**\n\n🎵 **Now Playing:** {current_song}\n\n**Up Next:**\n"
            
            for i, song in enumerate(self.queue[chat_id]):
                queue_msg += f"{i+1}. {song['title']} ({song['duration']})\n"
            
            return queue_msg
                
        except Exception as e:
            logger.error(f"Error in queue function: {e}")
            return f"❌ Error getting queue: {str(e)}"
            
    async def volume(self, chat_id: int, volume: int):
        """
        Change the volume of the current playback
        
        Args:
            chat_id (int): Chat ID where to change volume
            volume (int): Volume level (0-100)
            
        Returns:
            str: Status message
        """
        try:
            if chat_id not in self.active_chats:
                return "❌ No active playback to adjust volume."
                
            try:
                await self.pytgcalls.change_volume_call(chat_id, volume)
                return f"🔊 Volume set to {volume}%."
            except Exception as e:
                logger.error(f"Error changing volume: {e}")
                return f"❌ Error changing volume: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in volume function: {e}")
            return f"❌ Error changing volume: {str(e)}"
