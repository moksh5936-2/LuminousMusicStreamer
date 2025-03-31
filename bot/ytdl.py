"""
YouTube-DL integration module for fetching video information from YouTube.
"""
import logging
import yt_dlp as youtube_dl

logger = logging.getLogger(__name__)

# Configure youtube-dl options for info extraction only
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

async def get_video_info(query):
    """
    Get video information from YouTube
    
    Args:
        query (str): YouTube search query or URL
    
    Returns:
        tuple: (title, duration, thumbnail_url, video_url) or None if error
    """
    try:
        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            logger.info(f"Extracting info for query: {query}")
            info = ydl.extract_info(query, download=False)
            
            # Handle playlist (take first entry)
            if 'entries' in info:
                if not info['entries']:
                    return None
                info = info['entries'][0]
                
            # Get video details
            title = info['title']
            duration_seconds = info.get('duration', 0)
            thumbnail = info.get('thumbnail', '')
            video_url = info.get('webpage_url', '')
            
            # Format duration as MM:SS
            minutes, seconds = divmod(duration_seconds, 60)
            duration = f"{minutes}:{seconds:02d}"
            
            logger.info(f"Found video: {title}")
            return title, duration, thumbnail, video_url
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None
