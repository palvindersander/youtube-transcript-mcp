from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import transcript_lib as tlib

# Initialize FastMCP server
mcp = FastMCP("transcript")

@mcp.tool()
async def get_transcript(url: str, language_code: Optional[str] = None, include_metadata: bool = True) -> str:
    """Get the transcript for a YouTube video with timestamps in ~10 second intervals.
    
    Args:
        url: YouTube video URL or ID
        language_code: Optional language code (e.g., 'en', 'es', 'fr')
        include_metadata: Whether to include video metadata in the response
    """
    try:
        # Extract video ID from URL
        video_id = tlib.get_video_id(url)
        
        result = ""
        
        # Include metadata if requested
        if include_metadata:
            try:
                metadata = tlib.get_video_metadata(video_id)
                result += f"--- Video Metadata ---\n"
                result += f"Title: {metadata['title']}\n"
                result += f"Author: {metadata['author']}\n"
                result += f"Channel URL: {metadata['channel_url']}\n\n"
                result += f"Description:\n{metadata['description']}\n\n"
                result += "--- Transcript ---\n"
            except tlib.TranscriptError as e:
                result += f"Error fetching metadata: {str(e)}\n\n"
        
        # Get transcript
        transcript = tlib.get_transcript(video_id, language_code)
        
        # Format with timestamps in ~10 second intervals
        result += tlib.format_transcript_text(transcript)
        return result
    except tlib.TranscriptError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_video_metadata(url: str) -> str:
    """Get metadata for a YouTube video.
    
    Args:
        url: YouTube video URL or ID
    """
    try:
        # Extract video ID from URL
        video_id = tlib.get_video_id(url)
        
        # Get metadata
        metadata = tlib.get_video_metadata(video_id)
        
        # Format the response
        result = f"--- Video Metadata ---\n"
        result += f"Title: {metadata['title']}\n"
        result += f"Author: {metadata['author']}\n" 
        result += f"Channel URL: {metadata['channel_url']}\n"
        result += f"Thumbnail URL: {metadata['thumbnail_url']}\n\n"
        result += f"Description:\n{metadata['description']}"
        
        return result
    except tlib.TranscriptError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_transcript_languages(url: str) -> str:
    """List available transcript languages for a YouTube video.
    
    Args:
        url: YouTube video URL or ID
    """
    try:
        # Extract video ID from URL
        video_id = tlib.get_video_id(url)
        
        # Get available languages
        languages = tlib.get_available_languages(video_id)
        
        if not languages:
            return "No transcripts available for this video."
        
        # Format the response
        result = "Available transcript languages:\n"
        for lang in languages:
            result += f"- {lang['language']} ({lang['language_code']})"
            if lang['is_generated']:
                result += " (auto-generated)"
            result += "\n"
            
        return result
    except tlib.TranscriptError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 