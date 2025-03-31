"""
Bot initialization module. Creates and configures the Telegram client.
"""
import logging
from pyrogram import Client
from bot.config import Config

logger = logging.getLogger(__name__)

def create_bot():
    """
    Create and configure the Telegram client
    
    Returns:
        Client: Pyrogram Client
    """
    # Create Pyrogram client
    client = Client(
        "LuminousMusicBot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        in_memory=True
    )
    
    # Register message handlers
    from bot.helpers import register_handlers
    register_handlers(client)
    
    logger.info("Bot created and handlers registered")
    return client
