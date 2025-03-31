"""
Configuration module for the bot. Loads environment variables.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for the bot"""
    
    # Pyrogram credentials
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Check if required variables are set
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set"""
        required_vars = ["API_ID", "API_HASH", "BOT_TOKEN"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please set them in .env file or environment")
            return False
        
        try:
            if cls.API_ID is not None:
                cls.API_ID = int(cls.API_ID)
            else:
                logger.error("API_ID is not set")
                return False
        except ValueError:
            logger.error("API_ID must be an integer")
            return False
            
        return True

# Validate configuration on import
if not Config.validate():
    logger.warning("Configuration validation failed, bot may not work correctly")
