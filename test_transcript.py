#!/usr/bin/env python3
"""
Test script for the YouTube transcript library.
Usage: python3 test_transcript.py <youtube_url_or_id> [language_code] [log_file]
"""

import sys
import json
import os
import datetime
from transcript_lib import (
    get_video_id,
    get_transcript,
    get_available_languages,
    get_video_metadata,
    format_transcript_text,
    format_transcript_json,
    TranscriptError
)

def print_usage():
    print("Usage: python3 test_transcript.py <youtube_url_or_id> [language_code] [log_file]")
    print("Example: python3 test_transcript.py https://www.youtube.com/watch?v=ELj2LLNP8Ak")
    print("Example: python3 test_transcript.py ELj2LLNP8Ak en")
    print("Example: python3 test_transcript.py ELj2LLNP8Ak en logs/transcript.log")

def log_message(log_file, message):
    """Write message to both console and log file."""
    print(message)
    if log_file:
        log_file.write(message + "\n")

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    url = sys.argv[1]
    language_code = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Default log file is logs/transcript_<video_id>_<timestamp>.log
    log_path = None
    if len(sys.argv) > 3:
        log_path = sys.argv[3]
    
    log_file = None
    try:
        # Extract video ID
        video_id = get_video_id(url)
        
        # Create log file if not specified
        if not log_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            log_path = f"logs/transcript_{video_id}_{timestamp}.log"
        
        # Open log file
        log_file = open(log_path, "w", encoding="utf-8")
        
        # Fetch video metadata
        log_message(log_file, f"YouTube Transcript Test - {datetime.datetime.now()}")
        log_message(log_file, f"Video ID: {video_id}")
        log_message(log_file, f"URL: {url}")
        
        # Get and display video metadata
        log_message(log_file, "\nFetching video metadata...")
        try:
            metadata = get_video_metadata(video_id)
            log_message(log_file, "\n--- Video Metadata ---")
            log_message(log_file, f"Title: {metadata['title']}")
            log_message(log_file, f"Author: {metadata['author']}")
            log_message(log_file, f"Channel URL: {metadata['channel_url']}")
            log_message(log_file, f"Thumbnail URL: {metadata['thumbnail_url']}")
            
            log_message(log_file, "\nDescription:")
            log_message(log_file, "-------------")
            log_message(log_file, metadata['description'])
        except TranscriptError as e:
            log_message(log_file, f"Error fetching metadata: {e}")
        
        # List available languages
        log_message(log_file, "\nFetching available languages...")
        try:
            languages = get_available_languages(video_id)
            log_message(log_file, "Available languages:")
            for lang in languages:
                log_message(log_file, f"- {lang['language']} ({lang['language_code']})" + 
                          (" (auto-generated)" if lang['is_generated'] else ""))
        except TranscriptError as e:
            log_message(log_file, f"Error fetching languages: {e}")
        
        # Get transcript
        log_message(log_file, "\nFetching transcript...")
        if language_code:
            log_message(log_file, f"Language: {language_code}")
        
        transcript = get_transcript(video_id, language_code)
        
        # Format transcript with timestamps in ~10 second intervals
        log_message(log_file, "\nTranscript (with timestamps):")
        log_message(log_file, "------------------------")
        
        # Format and display transcript
        formatted_transcript = format_transcript_text(transcript)
        
        # Show first 5 lines in console, full transcript in log file
        transcript_lines = formatted_transcript.split('\n')
        console_preview = '\n'.join(transcript_lines[:5]) + "\n... (truncated)"
        print(console_preview)
        
        # Write full transcript to log file
        log_file.write(formatted_transcript + "\n")
        
        # Also store raw transcript data in JSON format in the log
        log_message(log_file, "\nRaw Transcript Data (JSON):")
        log_message(log_file, "------------------------")
        log_file.write(format_transcript_json(transcript) + "\n")
        
        # Count segments in raw and merged format
        raw_segments = len(transcript)
        merged_segments = len(transcript_lines)
        log_message(log_file, f"\nRaw transcript has {raw_segments} segments")
        log_message(log_file, f"Merged transcript has {merged_segments} segments (~10s intervals)")
        log_message(log_file, f"Results saved to {log_path}")
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