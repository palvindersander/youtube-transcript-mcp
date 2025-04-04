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
                result += f"Channel URL: {metadata['channel_url']}\n"
                
                # Get video statistics if available
                try:
                    stats = tlib.get_video_statistics(video_id)
                    if stats.get('views'):
                        result += f"View count: {stats['views']}\n"
                    if stats.get('likes'):
                        result += f"Likes: {stats['likes']}\n"
                    if stats.get('upload_date'):
                        result += f"Upload date: {stats['upload_date']}\n"
                except Exception:
                    # Skip statistics if not available
                    pass
                
                result += f"\nDescription:\n{metadata['description']}\n\n"
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
async def get_video_metadata(url: str, include_statistics: bool = True) -> str:
    """Get metadata for a YouTube video.
    
    Args:
        url: YouTube video URL or ID
        include_statistics: Whether to include view count, likes, and other stats
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
        result += f"Thumbnail URL: {metadata['thumbnail_url']}\n"
        
        # Include statistics if requested
        if include_statistics:
            try:
                stats = tlib.get_video_statistics(video_id)
                if stats:
                    result += "\n--- Video Statistics ---\n"
                    if stats.get('views'):
                        result += f"View count: {stats['views']}\n"
                    if stats.get('likes'):
                        result += f"Likes: {stats['likes']}\n"
                    if stats.get('upload_date'):
                        result += f"Upload date: {stats['upload_date']}\n"
            except Exception:
                # Skip statistics if there's an error
                pass
        
        result += f"\nDescription:\n{metadata['description']}"
        
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