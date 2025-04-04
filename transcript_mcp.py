from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import transcript_lib as tlib

# Initialize FastMCP server
mcp = FastMCP("transcript")

@mcp.tool()
async def get_transcript(url: str, language_code: Optional[str] = None, include_metadata: bool = True, identify_speakers: bool = False, speaker_hints: Optional[List[str]] = None) -> str:
    """Get the transcript for a YouTube video with timestamps in ~10 second intervals.
    
    Args:
        url: YouTube video URL or ID
        language_code: Optional language code (e.g., 'en', 'es', 'fr')
        include_metadata: Whether to include video metadata in the response
        identify_speakers: Whether to attempt to identify speakers in the transcript
        speaker_hints: Optional list of speaker names to look for in the transcript
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
        
        # Identify speakers if requested
        if identify_speakers:
            transcript_with_speakers, speakers = tlib.identify_speakers(transcript, speaker_hints)
            
            # Add speaker information to the output
            if speakers:
                result += f"--- Identified Speakers ({len(speakers)}) ---\n"
                for speaker, occurrences in speakers.items():
                    result += f"- {speaker}: {len(occurrences)} segments\n"
                result += "\n"
                
            # Format with timestamps and speakers
            result += tlib.format_transcript_with_speakers(transcript_with_speakers)
        else:
            # Format with timestamps in ~10 second intervals (standard format)
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

@mcp.tool()
async def identify_transcript_speakers(url: str, language_code: Optional[str] = None, speaker_hints: Optional[List[str]] = None) -> str:
    """Identify potential speakers in a YouTube video transcript.
    
    Args:
        url: YouTube video URL or ID
        language_code: Optional language code (e.g., 'en', 'es', 'fr')
        speaker_hints: Optional list of speaker names to look for in the transcript
    """
    try:
        # Extract video ID from URL
        video_id = tlib.get_video_id(url)
        
        # Get metadata
        try:
            metadata = tlib.get_video_metadata(video_id)
            result = f"--- Video Metadata ---\n"
            result += f"Title: {metadata['title']}\n"
            result += f"Author: {metadata['author']}\n\n"
        except tlib.TranscriptError as e:
            result = f"Error fetching metadata: {str(e)}\n\n"
        
        # Get transcript
        transcript = tlib.get_transcript(video_id, language_code)
        
        # Identify speakers
        transcript_with_speakers, speakers = tlib.identify_speakers(transcript, speaker_hints)
        
        # Report on identified speakers
        if speakers:
            result += f"--- Identified Speakers ({len(speakers)}) ---\n"
            for speaker, occurrences in speakers.items():
                result += f"- {speaker}: {len(occurrences)} segments\n"
        else:
            result += "No speakers identified using pattern matching.\n"
        
        # Format transcript with speakers
        result += "\n--- Transcript with Speaker Labels ---\n"
        result += tlib.format_transcript_with_speakers(transcript_with_speakers)
        
        return result
    except tlib.TranscriptError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 