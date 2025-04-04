from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import transcript_lib as tlib
import json
import os

# Import the new modules for fact-checking
import search_api
import transcript_segment

# Initialize FastMCP server
mcp = FastMCP("transcript")

# Initialize search client (will use environment variable for API key)
search_client = None

# Initialize on first use to avoid errors if API key not set
def get_search_client():
    global search_client
    if search_client is None:
        api_key = os.environ.get("SEARCH_API_KEY")
        # Enable mock mode if no API key is available
        mock_mode = api_key is None
        search_client = search_api.create_search_client(api_key=api_key, mock_mode=mock_mode)
    return search_client

@mcp.tool()
async def get_transcript(url: str, language_code: Optional[str] = None, include_metadata: bool = True, 
                         include_chapters: bool = True) -> str:
    """Get the transcript for a YouTube video with timestamps in ~10 second intervals.
    
    Args:
        url: YouTube video URL or ID
        language_code: Optional language code (e.g., 'en', 'es')
        include_metadata: Whether to include video metadata (default: True)
        include_chapters: Whether to include chapter markers in the transcript (default: True)
    """
    try:
        # Extract video ID from URL
        video_id = tlib.get_video_id(url)
        result = ""
        
        # Add metadata if requested
        if include_metadata:
            try:
                metadata = tlib.get_video_metadata(video_id)
                stats = tlib.get_video_statistics(video_id)
                
                result += f"--- Video Metadata ---\n"
                result += f"Title: {metadata['title']}\n"
                result += f"Author: {metadata['author']}\n"
                result += f"Channel URL: {metadata['channel_url']}\n"
                
                if stats:
                    if stats['views']:
                        result += f"Views: {stats['views']}\n"
                    if stats['likes']:
                        result += f"Likes: {stats['likes']}\n"
                    if stats['upload_date']:
                        result += f"Upload date: {stats['upload_date']}\n"
                
                if metadata.get('description'):
                    result += f"\nDescription:\n{metadata['description']}\n"
                
                result += "\n"
            except tlib.TranscriptError as e:
                result += f"Error fetching metadata: {str(e)}\n\n"
        
        # Get chapters if requested
        chapters = None
        if include_chapters:
            try:
                chapters = tlib.get_chapter_markers(video_id)
                
                # Add chapter markers at the top
                if chapters:
                    result += f"--- Chapter Markers ---\n"
                    for chapter in chapters:
                        result += f"[{chapter['start_time_formatted']}] {chapter['title']}\n"
                    result += "\n"
            except Exception:
                # Continue without chapters if there's an error
                pass
        
        # Get transcript
        transcript = tlib.get_transcript(video_id, language_code)
        
        # Format with timestamps in ~10 second intervals and include chapters if available
        result += tlib.format_transcript_text(transcript, chapters)
            
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

@mcp.tool()
async def get_chapter_markers(url: str) -> str:
    """Get chapter markers for a YouTube video.
    
    Args:
        url: YouTube video URL or ID
    """
    try:
        # Extract video ID from URL
        video_id = tlib.get_video_id(url)
        
        # Get chapter markers
        chapters = tlib.get_chapter_markers(video_id)
        
        if not chapters:
            return "No chapter markers found for this video."
        
        # Format the response
        result = f"--- Chapter Markers ---\n"
        for chapter in chapters:
            result += f"[{chapter['start_time_formatted']}] {chapter['title']}\n"
            
        return result
    except tlib.TranscriptError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# New tool: Search for claim verification
@mcp.tool()
async def search_for_claim_verification(claim: str, context: Optional[str] = None) -> str:
    """Search for information to help verify a claim made in a video.
    
    Args:
        claim: The specific claim to verify (a statement that can be true or false)
        context: Optional context from the video to help with the search
    """
    try:
        client = get_search_client()
        results = await client.search_for_claim_verification(claim, context)
        
        # Add a note if using mock mode
        if results.get("mock_mode", False):
            mock_notice = "\n[NOTE: Using mock search results for demonstration purposes. To use real search results, set the SEARCH_API_KEY environment variable.]\n"
            # Format as JSON string for Claude to parse
            json_results = json.dumps(results, indent=2)
            return mock_notice + json_results
        
        # Format as JSON string for Claude to parse
        return json.dumps(results, indent=2)
    except search_api.SearchAPIError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# New tool: Extract transcript segment
@mcp.tool()
async def extract_transcript_segment(url: str, timestamp: str, context_seconds: int = 30) -> str:
    """Extract a specific segment of a transcript around a timestamp.
    
    Args:
        url: YouTube video URL or ID
        timestamp: Timestamp in format MM:SS or HH:MM:SS
        context_seconds: Number of seconds of context before and after (default: 30)
    """
    try:
        segment_data = transcript_segment.extract_transcript_segment(
            url, timestamp, context_seconds
        )
        
        # Format response as readable text
        result = f"--- Transcript Segment at {timestamp} ---\n"
        result += f"Video: {segment_data['video_title']}\n"
        result += f"Author: {segment_data['author']}\n"
        
        if segment_data['chapter']:
            result += f"Chapter: {segment_data['chapter']}\n"
        
        result += f"Context: {context_seconds} seconds before and after\n\n"
        result += segment_data['segment']
        
        return result
    except tlib.TranscriptError as e:
        return f"Error: {str(e)}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# New tool: Find claim in transcript
@mcp.tool()
async def find_claim_in_transcript(url: str, claim: str, fuzzy_match: bool = True) -> str:
    """Find a specific claim in a transcript and return its timestamp and context.
    
    Args:
        url: YouTube video URL or ID
        claim: The claim to find
        fuzzy_match: Whether to use fuzzy matching (more lenient, default: True)
    """
    try:
        # Extract video ID
        video_id = tlib.get_video_id(url)
        
        # Get transcript
        transcript = tlib.get_transcript(video_id)
        
        # Find claim
        result = transcript_segment.find_claim_in_transcript(transcript, claim, fuzzy_match)
        
        if result:
            # Format response
            response = f"Found claim at timestamp: {result['timestamp']}\n\n"
            response += f"Context: {result['context']}\n\n"
            
            if 'match_score' in result:
                response += f"Note: This is a fuzzy match with {int(result['match_score'] * 100)}% confidence.\n"
            
            # Add a segment of the transcript around this point for context
            segment_data = transcript_segment.extract_transcript_segment(
                url, result['timestamp'], 30
            )
            
            response += f"\n--- Surrounding Transcript ---\n"
            response += segment_data['segment']
            
            return response
        else:
            return f"Claim not found in transcript. Try rephrasing or use fuzzy matching."
    except tlib.TranscriptError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 