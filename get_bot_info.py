"""
Temporary script to get bot information
"""
import os
import asyncio
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

async def get_bot_info():
    # Get API credentials from environment
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    bot_token = os.getenv("BOT_TOKEN")
    
    if not all([api_id, api_hash, bot_token]):
        print("Error: Missing API credentials")
        return
    
    # Create temporary client
    client = Client(
        "temp_session",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        in_memory=True
    )
    
    try:
        # Start the client
        await client.start()
        
        # Get bot information
        me = await client.get_me()
        print(f"Bot Username: @{me.username}")
        print(f"Bot Name: {me.first_name}")
        print(f"Bot ID: {me.id}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop the client
        await client.stop()

if __name__ == "__main__":
    asyncio.run(get_bot_info())