#!/usr/bin/env python3
"""
Test script for YouTube chapter markers functionality.
Usage: python3 test_chapter_markers.py <youtube_url_or_id> [log_file] [--debug]
"""

import sys
import json
import os
import datetime
import re
import requests
from transcript_lib import get_video_id, TranscriptError

def print_usage():
    print("Usage: python3 test_chapter_markers.py <youtube_url_or_id> [log_file] [--debug]")
    print("Example: python3 test_chapter_markers.py https://www.youtube.com/watch?v=ELj2LLNP8Ak")
    print("Example: python3 test_chapter_markers.py ELj2LLNP8Ak logs/chapters.log")
    print("Example: python3 test_chapter_markers.py ELj2LLNP8Ak --debug")

def log_message(log_file, message):
    """Write message to both console and log file."""
    print(message)
    if log_file:
        log_file.write(message + "\n")

def extract_chapter_markers(video_id, debug=False):
    """Extract chapter markers from a YouTube video.
    
    Args:
        video_id: YouTube video ID
        debug: Whether to print debug information
        
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
        
        if debug:
            print(f"Fetching URL: {watch_url}")
            
        response = requests.get(watch_url, headers=headers)
        response.raise_for_status()
        
        html_content = response.text
        
        if debug:
            print(f"Response length: {len(html_content)} characters")
            
        # Multiple methods to find chapters, as YouTube's structure can vary
        chapters = []
        
        # Method 0: FIRST APPROACH - Parse From Description Directly
        if debug:
            print("\nMethod 0: Directly parsing description for timestamps...")
        
        # Extract description - try to find it directly in the page
        full_description = ""
        
        # Method A: Get description from meta tag
        description_match = re.search(r'<meta name="description" content="([^"]*)"', html_content)
        if description_match:
            if debug:
                print("Found description in meta tag")
            full_description = description_match.group(1)
        
        # Method B: Get description from JSON data - often more complete
        if not full_description or len(full_description) < 50:
            desc_json_match = re.search(r'"description":{"simpleText":"(.*?)"},"', html_content)
            if desc_json_match:
                if debug:
                    print("Found description in JSON data")
                # Unescape the description
                full_description = desc_json_match.group(1).replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        
        # Method C: Look for videoDescription
        if not full_description or len(full_description) < 50:
            video_desc_match = re.search(r'"videoDescriptionText":\s*{\s*"runs":\s*(\[.*?\])', html_content)
            if video_desc_match:
                if debug:
                    print("Found description in videoDescriptionText")
                try:
                    desc_json = json.loads(video_desc_match.group(1))
                    # Join all text parts
                    full_description = "".join(run.get("text", "") for run in desc_json)
                except (json.JSONDecodeError, KeyError) as e:
                    if debug:
                        print(f"Error parsing description JSON: {e}")
        
        if full_description:
            if debug:
                print(f"Description length: {len(full_description)} characters")
                if len(full_description) > 200:
                    print(f"Description preview: {full_description[:200]}...")
                else:
                    print(f"Description: {full_description}")
            
            # Look for patterns in the description
            # Format 1: "00:00 Title", Format 2: "00:00 - Title", Format 3: "00:00: Title"
            timestamp_matches = re.finditer(r'((?:\d+:)?\d+:\d+)\s*(?:[-:])?\s*([^\n]+)', full_description)
            
            for match in timestamp_matches:
                timestamp_str = match.group(1)
                title = match.group(2).strip()
                
                # Convert timestamp to seconds
                seconds = parse_timestamp(timestamp_str)
                
                if seconds is not None and title:
                    if debug:
                        print(f"Found chapter in description: '{title}' at {timestamp_str}")
                        
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
                    if debug:
                        print("These might not be chapter markers - could be just timestamps in the description")
        
        # Method 1: Try to find the chapterSection which contains the chapter info
        if not chapters:
            if debug:
                print("\nMethod 1: Looking for chapter sections in JSON data...")
            
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
            
            for match_idx, match in enumerate(chapter_section_matches):
                if match:
                    if debug:
                        print(f"Found potential chapter data (pattern {match_idx+1})")
                    
                    try:
                        # Attempt to extract timestamps and titles from the match
                        json_text = match.group(1)
                        
                        if debug:
                            print(f"JSON text length: {len(json_text)} characters")
                            print(f"JSON text preview: {json_text[:100]}...")
                        
                        # Try to extract "title" and "timeRangeStartMillis" from the JSON data
                        title_matches = re.finditer(r'"title":[^}]*"simpleText":"([^"]*)"', json_text)
                        time_matches = re.finditer(r'"timeRangeStartMillis":"?(\d+)"?', json_text)
                        
                        titles = [m.group(1) for m in title_matches]
                        times = [int(m.group(1)) / 1000 for m in time_matches]  # Convert to seconds
                        
                        if debug:
                            print(f"Found {len(titles)} titles and {len(times)} timestamps")
                        
                        # If we have matching numbers of titles and times
                        if titles and times and len(titles) == len(times):
                            for i in range(len(titles)):
                                title = titles[i]
                                seconds = times[i]
                                
                                if debug:
                                    print(f"Found chapter: '{title}' at {format_timestamp(seconds)}")
                                
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
                                    if debug:
                                        print(f"Found chapter via regex: '{title}' at {timestamp_str}")
                                    
                                    chapters.append({
                                        'title': title,
                                        'start_time': seconds,
                                        'start_time_formatted': format_timestamp(seconds)
                                    })
                    except Exception as e:
                        if debug:
                            print(f"Error parsing chapter data: {e}")
            
            # If chapters were found, clean them up for duplicates and sort
            if chapters:
                # Remove duplicates (sometimes timestamps appear in multiple places)
                unique_chapters = []
                seen_times = set()
                
                for chapter in chapters:
                    if chapter['start_time'] not in seen_times:
                        seen_times.add(chapter['start_time'])
                        unique_chapters.append(chapter)
                
                chapters = unique_chapters
                if debug:
                    print(f"Found {len(chapters)} unique chapter timestamps")
        
        # Organize remaining methods - remove the old implementation and use the new methods
        
        # Method 2: Try to find chapter data in the initial player response
        if not chapters:
            if debug:
                print("\nMethod 2: Searching for chapter data in ytInitialPlayerResponse...")
                
            initial_data_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html_content, re.DOTALL)
            if initial_data_match:
                if debug:
                    print("Found ytInitialPlayerResponse, parsing JSON...")
                    
                try:
                    initial_data = json.loads(initial_data_match.group(1))
                    
                    # Look for chapters in playerOverlays
                    if 'playerOverlays' in initial_data:
                        if debug:
                            print("Found playerOverlays in initial data")
                            
                        player_overlays = initial_data['playerOverlays']
                        if 'playerOverlayRenderer' in player_overlays:
                            overlay_renderer = player_overlays['playerOverlayRenderer']
                            
                            # Look for chapters in decorated player bar
                            if 'decoratedPlayerBarRenderer' in overlay_renderer:
                                if debug:
                                    print("Found decoratedPlayerBarRenderer")
                                    
                                decorated_bar = overlay_renderer['decoratedPlayerBarRenderer']
                                if 'decoratedPlayerBarRenderer' in decorated_bar:
                                    player_bar = decorated_bar['decoratedPlayerBarRenderer']
                                    
                                    if 'playerBar' in player_bar:
                                        if 'chapteredPlayerBarRenderer' in player_bar['playerBar']:
                                            chaptered_bar = player_bar['playerBar']['chapteredPlayerBarRenderer']
                                            
                                            if 'chapters' in chaptered_bar:
                                                if debug:
                                                    print(f"Found chapters array with {len(chaptered_bar['chapters'])} items")
                                                    
                                                for chapter_data in chaptered_bar['chapters']:
                                                    if 'chapterRenderer' in chapter_data:
                                                        renderer = chapter_data['chapterRenderer']
                                                        title = renderer.get('title', {}).get('simpleText', 'Unknown Chapter')
                                                        time_millis = int(renderer.get('timeRangeStartMillis', 0))
                                                        
                                                        # Convert to seconds
                                                        time_seconds = time_millis / 1000
                                                        if debug:
                                                            print(f"Found chapter: '{title}' at {format_timestamp(time_seconds)}")
                                                            
                                                        chapters.append({
                                                            'title': title,
                                                            'start_time': time_seconds,
                                                            'start_time_formatted': format_timestamp(time_seconds)
                                                        })
                except (json.JSONDecodeError, KeyError) as e:
                    if debug:
                        print(f"Error parsing player response data: {e}")
                    log_message(None, f"Error parsing player response data: {e}")
        
        # Method 3: Look for structured data with chapter information
        if not chapters:
            if debug:
                print("\nMethod 3: Searching for chapters in ld+json structured data...")
                
            structured_data_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.DOTALL)
            if structured_data_match:
                if debug:
                    print("Found application/ld+json data")
                    
                try:
                    structured_data = json.loads(structured_data_match.group(1))
                    
                    # Check if this is a video with chapters
                    if isinstance(structured_data, dict):
                        if debug:
                            print(f"Keys in structured data: {', '.join(structured_data.keys())}")
                            
                        if 'hasPart' in structured_data:
                            if debug:
                                print(f"Found hasPart with {len(structured_data['hasPart'])} items")
                                
                            parts = structured_data['hasPart']
                            for part in parts:
                                if 'name' in part and 'startOffset' in part:
                                    title = part['name']
                                    # StartOffset is in seconds
                                    time_seconds = float(part['startOffset'])
                                    
                                    if debug:
                                        print(f"Found chapter: '{title}' at {format_timestamp(time_seconds)}")
                                        
                                    chapters.append({
                                        'title': title,
                                        'start_time': time_seconds,
                                        'start_time_formatted': format_timestamp(time_seconds)
                                    })
                except (json.JSONDecodeError, KeyError) as e:
                    if debug:
                        print(f"Error parsing structured data: {e}")
                    log_message(None, f"Error parsing structured data: {e}")
        
        # Sort and return chapters
        if chapters:
            chapters.sort(key=lambda x: x['start_time'])
            if debug:
                print(f"\nTotal chapters found: {len(chapters)}")
        elif debug:
            print("\nNo chapters found by any method")
        
        return chapters
    
    except Exception as e:
        if debug:
            import traceback
            traceback.print_exc()
        raise TranscriptError(f"Failed to extract chapter markers: {str(e)}")

def parse_timestamp(timestamp_str):
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

def format_timestamp(seconds):
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

def add_chapters_to_transcript(transcript_text, chapters):
    """Add chapter markers to a transcript.
    
    Args:
        transcript_text: Formatted transcript text with timestamps
        chapters: List of chapter markers
        
    Returns:
        Transcript with chapter markers inserted
    """
    if not chapters:
        return transcript_text
    
    # Split transcript into lines
    lines = transcript_text.split('\n')
    result = []
    
    # Add chapter markers to transcript
    next_chapter_index = 0
    
    for line in lines:
        # Extract timestamp from line
        timestamp_match = re.match(r'\[(\d+):(\d+)\]', line)
        
        if timestamp_match:
            minutes, seconds = map(int, timestamp_match.groups())
            line_time = minutes * 60 + seconds
            
            # Add any chapters that should appear before this line
            while (next_chapter_index < len(chapters) and 
                   chapters[next_chapter_index]['start_time'] <= line_time):
                
                chapter = chapters[next_chapter_index]
                chapter_line = f"\n[CHAPTER] {chapter['start_time_formatted']} - {chapter['title']}\n"
                result.append(chapter_line)
                next_chapter_index += 1
        
        result.append(line)
    
    return '\n'.join(result)

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    url = sys.argv[1]
    debug_mode = "--debug" in sys.argv
    
    # Get log file path if specified (but not if it's --debug)
    log_path = None
    for arg in sys.argv[2:]:
        if arg != "--debug":
            log_path = arg
            break
    
    log_file = None
    try:
        # Extract video ID
        video_id = get_video_id(url)
        
        # Create log file if not specified
        if not log_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            log_path = f"logs/chapters_{video_id}_{timestamp}.log"
        
        # Open log file
        log_file = open(log_path, "w", encoding="utf-8")
        
        log_message(log_file, f"YouTube Chapter Markers Test - {datetime.datetime.now()}")
        log_message(log_file, f"Video ID: {video_id}")
        log_message(log_file, f"URL: {url}")
        log_message(log_file, f"Debug Mode: {'Enabled' if debug_mode else 'Disabled'}")
        
        # Extract chapter markers
        log_message(log_file, "\nExtracting chapter markers...")
        chapters = extract_chapter_markers(video_id, debug=debug_mode)
        
        if chapters:
            log_message(log_file, f"\nFound {len(chapters)} chapter markers:")
            log_message(log_file, "-------------------------")
            
            for i, chapter in enumerate(chapters, 1):
                log_message(log_file, f"{i}. [{chapter['start_time_formatted']}] {chapter['title']}")
            
            # Save chapters as JSON
            log_message(log_file, "\nChapter markers (JSON):")
            log_message(log_file, "-----------------------")
            log_file.write(json.dumps(chapters, indent=2) + "\n")
            
            # Example of adding chapters to a transcript
            log_message(log_file, "\nExample of how chapters would be added to a transcript:")
            log_message(log_file, "---------------------------------------------------")
            example_transcript = "[00:00] This is the start of the video.\n[00:15] Some more content here.\n[01:30] Later in the video."
            log_message(log_file, add_chapters_to_transcript(example_transcript, chapters))
            
        else:
            log_message(log_file, "No chapter markers found for this video.")
        
        log_message(log_file, f"\nResults saved to {log_path}")
        return 0
        
    except TranscriptError as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        if log_file:
            log_file.write(error_msg + "\n")
        return 1
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        if log_file:
            log_file.write(error_msg + "\n")
        return 1
    finally:
        if log_file:
            log_file.close()

if __name__ == "__main__":
    sys.exit(main()) 