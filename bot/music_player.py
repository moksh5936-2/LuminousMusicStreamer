"""
Music player module that handles voice chat streaming with PyTgCalls
"""
import logging
import asyncio
from pytgcalls import PyTgCalls, types
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.exceptions import GroupCallNotFound, NoActiveGroupCall
from pyrogram import Client
from pyrogram.errors import ChatAdminRequired, UserNotParticipant
from bot.ytdl import download_and_extract_audio

logger = logging.getLogger(__name__)

class MusicPlayer:
    """
    Music player class to handle voice chat streaming in multiple groups
    """
    def __init__(self, client: Client, session_string: str):
        """
        Initialize the music player
        
        Args:
            client (pyrogram.Client): Pyrogram client
            session_string (str): Pyrogram session string for PyTgCalls
        """
        # Initialize PyTgCalls client
        self.pytgcalls = PyTgCalls(client)
        
        # Dictionary to track active streams by chat_id
        self.active_chats = {}
        
        # Start PyTgCalls
        self.pytgcalls.start()
        
        logger.info("Music player initialized")
    
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
            # Download audio from YouTube
            logger.info(f"Downloading audio for query: {query}")
            audio_info = await download_and_extract_audio(query)
            
            if not audio_info:
                return "❌ Could not find or download the requested song."
            
            audio_file, title, duration, thumbnail = audio_info
            
            # Try to join the voice chat
            try:
                await self.pytgcalls.join_group_call(
                    chat_id,
                    InputAudioStream(
                        audio_file,
                        tgcalls_path=audio_file,  # Set the FFmpeg file path
                    ),
                    stream_type=types.StreamType().local_stream,
                )
                
                # Update active chats dictionary
                self.active_chats[chat_id] = {
                    'audio_file': audio_file,
                    'title': title,
                    'duration': duration
                }
                
                logger.info(f"Started playing in chat {chat_id}: {title}")
                return f"🎵 **Now playing:** {title}\n⏱ **Duration:** {duration}\n\n🎧 Enjoy the music!"
                
            except NoActiveGroupCall:
                return "❌ No active group call found. Please start a voice chat first!"
            
            except ChatAdminRequired:
                return "❌ I need to be an admin in this chat to play music!"
                
            except Exception as e:
                logger.error(f"Error joining voice chat: {e}")
                return f"❌ Error joining voice chat: {str(e)}"
                
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
                # Leave the group call
                await self.pytgcalls.leave_group_call(chat_id)
                
                # Clean up
                self.active_chats.pop(chat_id, None)
                
                logger.info(f"Stopped playing in chat {chat_id}")
                return "🛑 Stopped playing and left the voice chat."
            else:
                return "❌ I'm not playing anything in this chat."
                
        except GroupCallNotFound:
            # If there's no active call, just clean up our tracking
            self.active_chats.pop(chat_id, None)
            return "❌ No active voice chat found."
            
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return f"❌ Error stopping playback: {str(e)}"
