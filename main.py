"""
LuminousMusicBot - A lightweight Telegram music bot for voice chat streaming.
Main entry point for the bot.
"""
import os
import logging
import threading
from flask import Flask
from app import app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_flask_app():
    """Run the Flask web application"""
    try:
        logger.info("Starting web interface...")
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error in web interface: {e}")

def run_telegram_bot():
    """Run the Telegram bot"""
    import asyncio
    from bot import create_bot
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting Telegram bot...")
        
        # Create and run the bot
        client = create_bot()
        
        # Start the bot
        loop.run_until_complete(client.start())
        
        # Idle to keep the bot running
        logger.info("Bot is now running!")
        loop.run_until_complete(client.idle())
        
    except Exception as e:
        logger.error(f"Error in Telegram bot: {e}")
    finally:
        # Cleanup
        if 'client' in locals() and 'loop' in locals():
            loop.run_until_complete(client.stop())
        logger.info("Bot stopped.")

if __name__ == "__main__":
    # Check if we're running in a web environment (gunicorn)
    is_web_env = 'GUNICORN_CMD_ARGS' in os.environ
    
    if is_web_env:
        # If running through gunicorn, just expose the Flask app
        logger.info("Running in web environment")
    else:
        # Otherwise, start both the bot and web interface
        logger.info("Starting both web interface and Telegram bot...")
        
        # Start the Flask app in a separate thread
        web_thread = threading.Thread(target=run_flask_app)
        web_thread.daemon = True
        web_thread.start()
        
        # Run the Telegram bot in the main thread
        run_telegram_bot()
