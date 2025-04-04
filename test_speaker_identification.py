#!/usr/bin/env python3
"""
Test script for speaker identification in YouTube transcripts.
Usage: python3 test_speaker_identification.py <youtube_url_or_id> [log_file]
"""

import sys
import os
import json
import datetime
import re
from transcript_lib import (
    get_video_id,
    get_transcript,
    get_video_metadata,
    identify_speakers,
    format_transcript_with_speakers,
    TranscriptError
)

def print_usage():
    print("Usage: python3 test_speaker_identification.py <youtube_url_or_id> [log_file]")
    print("Example: python3 test_speaker_identification.py https://www.youtube.com/watch?v=ELj2LLNP8Ak")
    print("Example: python3 test_speaker_identification.py ELj2LLNP8Ak logs/speaker.log")

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
    
    # Default log file is logs/speaker_<video_id>_<timestamp>.log
    log_path = None
    if len(sys.argv) > 2:
        log_path = sys.argv[2]
    
    log_file = None
    try:
        # Extract video ID
        video_id = get_video_id(url)
        
        # Create log file if not specified
        if not log_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            log_path = f"logs/speaker_{video_id}_{timestamp}.log"
        
        # Open log file
        log_file = open(log_path, "w", encoding="utf-8")
        
        log_message(log_file, f"YouTube Speaker Identification Test - {datetime.datetime.now()}")
        log_message(log_file, f"Video ID: {video_id}")
        log_message(log_file, f"URL: {url}")
        
        # Get video metadata
        try:
            log_message(log_file, "\nFetching video metadata...")
            metadata = get_video_metadata(video_id)
            log_message(log_file, f"Title: {metadata.get('title', 'Not available')}")
            log_message(log_file, f"Author: {metadata.get('author', 'Not available')}")
        except Exception as e:
            log_message(log_file, f"Could not fetch metadata: {str(e)}")
        
        # Get transcript
        log_message(log_file, "\nFetching transcript...")
        transcript = get_transcript(video_id)
        
        # Identify speakers
        log_message(log_file, "\nIdentifying potential speakers...")
        transcript_with_speakers, speakers = identify_speakers(transcript)
        
        # Report on identified speakers
        if speakers:
            log_message(log_file, f"\nFound {len(speakers)} potential speakers:")
            for speaker, occurrences in speakers.items():
                log_message(log_file, f"- {speaker}: {len(occurrences)} occurrences")
        else:
            log_message(log_file, "\nNo speakers identified using pattern matching.")
        
        # Format transcript with speakers
        log_message(log_file, "\nTranscript with speakers:")
        log_message(log_file, "------------------------")
        formatted_transcript = format_transcript_with_speakers(transcript_with_speakers)
        
        # Show first 5 lines in console, full transcript in log file
        transcript_lines = formatted_transcript.split('\n')
        preview_lines = min(5, len(transcript_lines))
        console_preview = '\n'.join(transcript_lines[:preview_lines])
        if len(transcript_lines) > preview_lines:
            console_preview += "\n... (truncated)"
        print(console_preview)
        
        # Write full transcript to log file
        log_file.write(formatted_transcript + "\n")
        
        # Also save raw transcript data with speakers in JSON format
        log_message(log_file, "\nRaw Transcript Data with Speakers (JSON):")
        log_message(log_file, "----------------------------------------")
        log_file.write(json.dumps(transcript_with_speakers, indent=2) + "\n")
        
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