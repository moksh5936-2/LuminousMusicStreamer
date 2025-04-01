"""
YouTube-DL integration module for fetching video information from YouTube.
"""
import logging
import os
import yt_dlp as youtube_dl
import asyncio
import tempfile

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

# Configure youtube-dl options for downloading
ytdl_download_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(id)s.%(ext)s',
    'noplaylist': True,
    'nocheckcertificate': True, 
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
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

async def download_and_extract_audio(query):
    """
    Download and extract audio from a YouTube video
    
    Args:
        query (str): YouTube search query or URL
    
    Returns:
        tuple: (audio_file_path, title, duration, thumbnail_url) or None if error
    """
    try:
        # First, get video info to show details to the user
        video_info = await get_video_info(query)
        if not video_info:
            return None
            
        title, duration, thumbnail, video_url = video_info
        
        # Create a temporary directory to store the audio file
        temp_dir = tempfile.mkdtemp()
        
        # Set the output template to the temp directory
        download_opts = ytdl_download_opts.copy()
        download_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')
        
        # Run the download in a separate thread to not block the main event loop
        def _download():
            with youtube_dl.YoutubeDL(download_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                # Handle playlist (take first entry)
                if 'entries' in info:
                    info = info['entries'][0]
                return info
                
        # Run the download function in a thread pool
        logger.info(f"Downloading audio for: {title}")
        info = await asyncio.to_thread(_download)
        
        # Get the path of the downloaded file
        audio_file = os.path.join(temp_dir, f"{info['id']}.mp3")
        
        if not os.path.exists(audio_file):
            logger.error(f"Downloaded file not found: {audio_file}")
            return None
            
        logger.info(f"Audio downloaded: {audio_file}")
        return audio_file, title, duration, thumbnail
        
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        return None
