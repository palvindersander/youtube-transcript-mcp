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

def get_video_statistics(video_id: str) -> Dict[str, Any]:
    """Fetch video statistics (view count, likes, upload date).
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary with statistics
        
    Raises:
        TranscriptError: If unable to fetch statistics
    """
    stats = {
        "views": None,
        "likes": None,
        "upload_date": None
    }
    
    try:
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(watch_url, headers=headers)
        response.raise_for_status()
        
        html_content = response.text
        
        # Extract view count
        view_count_match = re.search(r'"viewCount":\s*"(\d+)"', html_content)
        if view_count_match:
            views = int(view_count_match.group(1))
            # Format with commas
            stats["views"] = f"{views:,}"
        
        # Extract like count
        like_count_match = re.search(r'"likeCount":\s*"(\d+)"', html_content)
        if like_count_match:
            likes = int(like_count_match.group(1))
            # Format with commas
            stats["likes"] = f"{likes:,}"
        
        # Extract upload date
        upload_date_match = re.search(r'"uploadDate":\s*"([^"]+)"', html_content)
        if upload_date_match:
            stats["upload_date"] = upload_date_match.group(1)
        
        return stats
    except Exception as e:
        # Don't raise an exception - stats are non-critical
        return stats

def get_chapter_markers(video_id: str) -> List[Dict[str, Any]]:
    """Extract chapter markers from a YouTube video.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        List of chapter markers with timestamps and titles
        
    Raises:
        TranscriptError: If unable to fetch or parse chapter markers
    """
    try:
        # Fetch the YouTube page
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(watch_url, headers=headers)
        response.raise_for_status()
        
        html_content = response.text
        
        # Multiple methods to find chapters, as YouTube's structure can vary
        chapters = []
        
        # Method 1: Try to extract description and look for timestamps
        full_description = ""
        
        # Try to get description from meta tag
        description_match = re.search(r'<meta name="description" content="([^"]*)"', html_content)
        if description_match:
            full_description = description_match.group(1)
        
        # Try to get description from JSON data - often more complete
        if not full_description or len(full_description) < 50:
            desc_json_match = re.search(r'"description":{"simpleText":"(.*?)"},"', html_content)
            if desc_json_match:
                # Unescape the description
                full_description = desc_json_match.group(1).replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        
        # Try to get description from videoDescriptionText
        if not full_description or len(full_description) < 50:
            video_desc_match = re.search(r'"videoDescriptionText":\s*{\s*"runs":\s*(\[.*?\])', html_content)
            if video_desc_match:
                try:
                    desc_json = json.loads(video_desc_match.group(1))
                    # Join all text parts
                    full_description = "".join(run.get("text", "") for run in desc_json)
                except (json.JSONDecodeError, KeyError):
                    pass
        
        if full_description:
            # Look for patterns in the description
            # Format 1: "00:00 Title", Format 2: "00:00 - Title", Format 3: "00:00: Title"
            timestamp_matches = re.finditer(r'((?:\d+:)?\d+:\d+)\s*(?:[-:])?\s*([^\n]+)', full_description)
            
            for match in timestamp_matches:
                timestamp_str = match.group(1)
                title = match.group(2).strip()
                
                # Convert timestamp to seconds
                seconds = parse_timestamp(timestamp_str)
                
                if seconds is not None and title:
                    chapters.append({
                        'title': title,
                        'start_time': seconds,
                        'start_time_formatted': format_timestamp(seconds)
                    })
            
            # If we found multiple chapters, make sure they start at 0
            if len(chapters) > 1:
                # Sort the chapters by start time
                chapters.sort(key=lambda x: x['start_time'])
                
                # Check if the first chapter starts at 0:00 or close to it
                if chapters[0]['start_time'] > 10:  # If first chapter is more than 10 seconds in
                    # These might not be chapter markers - could be just timestamps
                    chapters = []
        
        # Method 2: Look for chapter sections in JSON data
        if not chapters:
            # Look for chapter section in various YouTube JSON formats
            chapter_section_matches = [
                # Format 1: chapterSectionRenderer
                re.search(r'"chapterSectionRenderer":\s*({.*?}),\s*"sectionListRenderer"', html_content),
                # Format 2: videoSections pattern
                re.search(r'"videoSections":\s*\[(.*?)\],', html_content),
                # Format 3: explicit chapters
                re.search(r'"chapters":\s*\[(.*?)\],', html_content),
                # Format 4: chapterRenderer from the main content
                re.search(r'"chapterRenderer"[^{]*(\{.*?\}\])', html_content)
            ]
            
            for match in chapter_section_matches:
                if match:
                    try:
                        # Attempt to extract timestamps and titles from the match
                        json_text = match.group(1)
                        
                        # Try to extract "title" and "timeRangeStartMillis" from the JSON data
                        title_matches = re.finditer(r'"title":[^}]*"simpleText":"([^"]*)"', json_text)
                        time_matches = re.finditer(r'"timeRangeStartMillis":"?(\d+)"?', json_text)
                        
                        titles = [m.group(1) for m in title_matches]
                        times = [int(m.group(1)) / 1000 for m in time_matches]  # Convert to seconds
                        
                        # If we have matching numbers of titles and times
                        if titles and times and len(titles) == len(times):
                            for i in range(len(titles)):
                                title = titles[i]
                                seconds = times[i]
                                
                                chapters.append({
                                    'title': title,
                                    'start_time': seconds,
                                    'start_time_formatted': format_timestamp(seconds)
                                })
                        else:
                            # Try more generic timestamp extraction
                            timestamp_matches = re.finditer(r'((?:\d+:)?\d+:\d+)[^a-zA-Z0-9]*([^",\[\]{}]*)', json_text)
                            
                            for t_match in timestamp_matches:
                                timestamp_str = t_match.group(1)
                                title = t_match.group(2).strip()
                                
                                # Convert timestamp to seconds
                                seconds = parse_timestamp(timestamp_str)
                                
                                if seconds is not None and title:
                                    chapters.append({
                                        'title': title,
                                        'start_time': seconds,
                                        'start_time_formatted': format_timestamp(seconds)
                                    })
                    except Exception:
                        continue
        
        # Method 3: Try to find chapter data in the ytInitialPlayerResponse
        if not chapters:
            initial_data_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html_content, re.DOTALL)
            if initial_data_match:
                try:
                    initial_data = json.loads(initial_data_match.group(1))
                    
                    # Check if chapters exist in the player response
                    if 'playerOverlays' in initial_data:
                        player_overlays = initial_data['playerOverlays']
                        if 'playerOverlayRenderer' in player_overlays:
                            overlay_renderer = player_overlays['playerOverlayRenderer']
                            if 'decoratedPlayerBarRenderer' in overlay_renderer:
                                decorated_bar = overlay_renderer['decoratedPlayerBarRenderer']
                                if 'decoratedPlayerBarRenderer' in decorated_bar:
                                    player_bar = decorated_bar['decoratedPlayerBarRenderer']
                                    if 'playerBar' in player_bar:
                                        if 'chapteredPlayerBarRenderer' in player_bar['playerBar']:
                                            chaptered_bar = player_bar['playerBar']['chapteredPlayerBarRenderer']
                                            if 'chapters' in chaptered_bar:
                                                for chapter_data in chaptered_bar['chapters']:
                                                    if 'chapterRenderer' in chapter_data:
                                                        renderer = chapter_data['chapterRenderer']
                                                        title = renderer.get('title', {}).get('simpleText', 'Unknown Chapter')
                                                        time_millis = int(renderer.get('timeRangeStartMillis', 0))
                                                        
                                                        # Convert to seconds
                                                        time_seconds = time_millis / 1000
                                                        chapters.append({
                                                            'title': title,
                                                            'start_time': time_seconds,
                                                            'start_time_formatted': format_timestamp(time_seconds)
                                                        })
                except (json.JSONDecodeError, KeyError):
                    pass
        
        # Method 4: Look for structured data with chapter information
        if not chapters:
            structured_data_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
            if structured_data_match:
                try:
                    structured_data = json.loads(structured_data_match.group(1))
                    
                    # Check if this is a video with chapters
                    if isinstance(structured_data, dict):
                        if 'hasPart' in structured_data:
                            parts = structured_data['hasPart']
                            for part in parts:
                                if 'name' in part and 'startOffset' in part:
                                    title = part['name']
                                    # StartOffset is in seconds
                                    time_seconds = float(part['startOffset'])
                                    
                                    chapters.append({
                                        'title': title,
                                        'start_time': time_seconds,
                                        'start_time_formatted': format_timestamp(time_seconds)
                                    })
                except (json.JSONDecodeError, KeyError):
                    pass
        
        # If chapters were found, clean them up for duplicates and sort
        if chapters:
            # Remove duplicates (sometimes timestamps appear in multiple places)
            unique_chapters = []
            seen_times = set()
            
            for chapter in chapters:
                if chapter['start_time'] not in seen_times:
                    seen_times.add(chapter['start_time'])
                    unique_chapters.append(chapter)
            
            # Sort by start time
            unique_chapters.sort(key=lambda x: x['start_time'])
            return unique_chapters
        
        return []
        
    except Exception as e:
        raise TranscriptError(f"Failed to extract chapter markers: {str(e)}")

def parse_timestamp(timestamp_str: str) -> Optional[int]:
    """Convert a timestamp string to seconds.
    
    Args:
        timestamp_str: Timestamp string (e.g., "1:23" or "1:23:45")
        
    Returns:
        Time in seconds or None if parsing fails
    """
    try:
        parts = timestamp_str.split(':')
        
        if len(parts) == 2:  # MM:SS format
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS format
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        
        return None
    except ValueError:
        return None

def format_timestamp(seconds: float) -> str:
    """Format seconds as a timestamp string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp (MM:SS or HH:MM:SS)
    """
    seconds = int(seconds)
    
    if seconds < 3600:  # Less than an hour
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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

def format_transcript_text(transcript: List[Dict[str, Any]], chapters: Optional[List[Dict[str, Any]]] = None) -> str:
    """Format transcript as text with timestamps, merging segments into ~10 second intervals.
    Optionally includes chapter markers.
    
    Args:
        transcript: List of transcript segments
        chapters: Optional list of chapter markers to include
        
    Returns:
        Formatted transcript text with timestamps in ~10 second intervals and optional chapter markers
    """
    if not transcript:
        return ""
    
    merged_segments = []
    current_text = ""
    current_start = transcript[0]["start"]
    current_duration = 0
    
    # If chapters are provided, prepare for insertion
    next_chapter_index = 0
    chapter_lines = []
    
    if chapters:
        chapters.sort(key=lambda x: x['start_time'])
    
    for segment in transcript:
        # If adding this segment would exceed ~10 seconds, start a new merged segment
        if current_duration > 0 and current_duration + segment["duration"] > 10:
            # Format time as MM:SS
            minutes = int(current_start / 60)
            seconds = int(current_start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            line_time = minutes * 60 + seconds
            
            # Add any chapters that should appear before this line if chapters are provided
            if chapters:
                while (next_chapter_index < len(chapters) and 
                       chapters[next_chapter_index]['start_time'] <= line_time):
                    
                    chapter = chapters[next_chapter_index]
                    chapter_line = f"\n[CHAPTER] {chapter['start_time_formatted']} - {chapter['title']}\n"
                    chapter_lines.append((line_time, chapter_line))
                    next_chapter_index += 1
            
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
    
    # Now insert the chapter markers at appropriate positions
    if chapters and chapter_lines:
        result = []
        segment_index = 0
        
        # Sort chapter lines by timestamp
        chapter_lines.sort(key=lambda x: x[0])
        
        for _, chapter_line in chapter_lines:
            while (segment_index < len(merged_segments) and 
                   segment_index < len(merged_segments)):
                result.append(merged_segments[segment_index])
                segment_index += 1
            
            result.append(chapter_line)
        
        # Add any remaining segments
        while segment_index < len(merged_segments):
            result.append(merged_segments[segment_index])
            segment_index += 1
        
        return "\n".join(result)
    
    return "\n".join(merged_segments)

def format_transcript_json(transcript: List[Dict[str, Any]]) -> str:
    """Format transcript as JSON.
    
    Args:
        transcript: List of transcript segments
        
    Returns:
        JSON formatted transcript
    """
    return json.dumps(transcript, indent=2) 