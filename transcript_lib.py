from typing import List, Dict, Any, Optional, Tuple
from youtube_transcript_api import YouTubeTranscriptApi
import json
import re
import requests

class TranscriptError(Exception):
    """Exception raised when transcript fetching fails."""
    pass

def get_video_id(url: str) -> str:
    """Extract video ID from a YouTube URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Video ID as a string
    """
    if "youtube.com/watch?v=" in url:
        video_id = url.split("youtube.com/watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    else:
        # If it's already an ID (no URL formatting), just return it
        video_id = url
    
    return video_id

def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """Fetch video metadata (title, description, author, etc.).
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary with metadata
        
    Raises:
        TranscriptError: If unable to fetch metadata
    """
    # First try oEmbed API to get the title
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    
    metadata = {
        "title": None,
        "description": None,
        "author": None,
        "channel_url": None,
        "thumbnail_url": None
    }
    
    try:
        response = requests.get(oembed_url)
        response.raise_for_status()
        data = response.json()
        
        metadata["title"] = data.get("title")
        metadata["author"] = data.get("author_name")
        metadata["channel_url"] = data.get("author_url")
        metadata["thumbnail_url"] = data.get("thumbnail_url")
    except Exception as e:
        raise TranscriptError(f"Failed to fetch metadata from oEmbed: {str(e)}")
    
    # Now try to get the description by parsing the watch page
    # This is more fragile but YouTube's API requires authentication
    try:
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(watch_url, headers=headers)
        response.raise_for_status()
        
        html_content = response.text
        
        # Try to find description in meta tags
        description_match = re.search(r'<meta name="description" content="([^"]*)"', html_content)
        if description_match:
            metadata["description"] = description_match.group(1)
        
        # If title wasn't found from oEmbed, try to extract from HTML
        if not metadata["title"]:
            title_match = re.search(r'<meta name="title" content="([^"]*)"', html_content)
            if title_match:
                metadata["title"] = title_match.group(1)
    except Exception as e:
        # Don't raise an exception for description - it's secondary
        metadata["description"] = f"Description unavailable: {str(e)}"
    
    return metadata

def get_available_languages(video_id: str) -> List[Dict[str, str]]:
    """Get list of available transcript languages for a video.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        List of dictionaries with language info
        
    Raises:
        TranscriptError: If unable to fetch transcript languages
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        languages = []
        
        # Get all available languages
        for transcript in transcript_list:
            languages.append({
                "language_code": transcript.language_code,
                "language": transcript.language,
                "is_generated": transcript.is_generated
            })
            
        return languages
    except Exception as e:
        raise TranscriptError(f"Failed to fetch available languages: {str(e)}")

def get_transcript(video_id: str, language_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get transcript for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        language_code: Language code to fetch (uses default if None)
        
    Returns:
        List of transcript segments
        
    Raises:
        TranscriptError: If unable to fetch transcript
    """
    try:
        if language_code:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language_code])
        else:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            
        return transcript
    except Exception as e:
        raise TranscriptError(f"Failed to fetch transcript: {str(e)}")

def format_transcript_text(transcript: List[Dict[str, Any]]) -> str:
    """Format transcript as text with timestamps, merging segments into ~10 second intervals.
    
    Args:
        transcript: List of transcript segments
        
    Returns:
        Formatted transcript text with timestamps in ~10 second intervals
    """
    if not transcript:
        return ""
    
    merged_segments = []
    current_text = ""
    current_start = transcript[0]["start"]
    current_duration = 0
    
    for segment in transcript:
        # If adding this segment would exceed ~10 seconds, start a new merged segment
        if current_duration > 0 and current_duration + segment["duration"] > 10:
            # Format time as MM:SS
            minutes = int(current_start / 60)
            seconds = int(current_start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            
            # Add the current merged segment to the result
            merged_segments.append(f"{timestamp} {current_text}")
            
            # Start a new segment
            current_text = segment["text"]
            current_start = segment["start"]
            current_duration = segment["duration"]
        else:
            # Add to the current segment
            if current_text:
                current_text += " " + segment["text"]
            else:
                current_text = segment["text"]
            current_duration += segment["duration"]
    
    # Add the last segment if there's anything left
    if current_text:
        minutes = int(current_start / 60)
        seconds = int(current_start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        merged_segments.append(f"{timestamp} {current_text}")
    
    return "\n".join(merged_segments)

def identify_speakers(transcript: List[Dict[str, Any]], speaker_hints: Optional[List[str]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, List[float]]]:
    """Identify potential speakers in a transcript.
    
    Args:
        transcript: List of transcript segments
        speaker_hints: Optional list of speaker names to look for
        
    Returns:
        Tuple containing:
        - Transcript with speaker labels
        - Dictionary of speakers with timestamps of their segments
    """
    # Define regex patterns for speaker identification
    patterns = [
        # Pattern 1: Name followed by colon (e.g., "John: Hello")
        r'^([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?):',
        
        # Pattern 2: Speaker in brackets (e.g., "[John] Hello")
        r'^\[([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?)\]',
        
        # Pattern 3: Speaker in parentheses (e.g., "(John) Hello")
        r'^\(([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)?)\)',
        
        # Pattern 4: "Speaker:" at beginning of line
        r'^(Speaker(?: \d+)?):',
        
        # Pattern 5: "Interviewer:" or "Interviewee:" or "Host:" or "Guest:"
        r'^(Interviewer|Interviewee|Host|Guest|Moderator|Participant(?: \d+)?):',
    ]
    
    # If speaker hints are provided, add them to patterns
    if speaker_hints:
        for speaker in speaker_hints:
            # Escape any regex special characters in the speaker name
            escaped_speaker = re.escape(speaker)
            # Add pattern for this speaker name followed by colon
            patterns.append(f'^({escaped_speaker}):')
    
    # Initialize result and detected speakers
    result = []
    speakers = {}
    
    # Process each segment
    for segment in transcript:
        text = segment['text']
        speaker = None
        
        # Try to identify speaker using patterns
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                speaker = match.group(1)
                # Remove speaker label from text
                text = re.sub(pattern, '', text).strip()
                break
        
        # If speaker was found, add to speakers dict
        if speaker:
            if speaker not in speakers:
                speakers[speaker] = []
            speakers[speaker].append(segment['start'])
        
        # Add segment to result with speaker if identified
        result_segment = segment.copy()
        result_segment['text'] = text
        if speaker:
            result_segment['speaker'] = speaker
        result.append(result_segment)
    
    return result, speakers

def format_transcript_with_speakers(transcript: List[Dict[str, Any]]) -> str:
    """Format transcript text with timestamps and speakers.
    
    Args:
        transcript: List of transcript segments with speaker labels
        
    Returns:
        Formatted transcript text with timestamps and speaker labels
    """
    formatted_lines = []
    
    for segment in transcript:
        # Format time as MM:SS
        minutes = int(segment['start'] / 60)
        seconds = int(segment['start'] % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        
        # Add speaker label if available
        if 'speaker' in segment:
            speaker_label = f" <{segment['speaker']}>"
        else:
            speaker_label = ""
        
        # Format line
        line = f"{timestamp}{speaker_label} {segment['text']}"
        formatted_lines.append(line)
    
    return "\n".join(formatted_lines)

def format_transcript_json(transcript: List[Dict[str, Any]]) -> str:
    """Format transcript as JSON.
    
    Args:
        transcript: List of transcript segments
        
    Returns:
        JSON formatted transcript
    """
    return json.dumps(transcript, indent=2) 