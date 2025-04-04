#!/usr/bin/env python3
"""
Test script for YouTube video statistics functionality.
Usage: python3 test_statistics.py <youtube_url_or_id> [log_file]
"""

import sys
import os
import datetime
from transcript_lib import (
    get_video_id,
    get_video_metadata,
    get_video_statistics,
    TranscriptError
)

def print_usage():
    print("Usage: python3 test_statistics.py <youtube_url_or_id> [log_file]")
    print("Example: python3 test_statistics.py https://www.youtube.com/watch?v=ELj2LLNP8Ak")
    print("Example: python3 test_statistics.py ELj2LLNP8Ak logs/stats.log")

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
    
    # Default log file is logs/stats_<video_id>_<timestamp>.log
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
            log_path = f"logs/stats_{video_id}_{timestamp}.log"
        
        # Open log file
        log_file = open(log_path, "w", encoding="utf-8")
        
        log_message(log_file, f"YouTube Video Statistics Test - {datetime.datetime.now()}")
        log_message(log_file, f"Video ID: {video_id}")
        log_message(log_file, f"URL: {url}")
        
        # Get and display basic video metadata
        try:
            metadata = get_video_metadata(video_id)
            log_message(log_file, "\n--- Basic Metadata ---")
            log_message(log_file, f"Title: {metadata['title']}")
            log_message(log_file, f"Author: {metadata['author']}")
            log_message(log_file, f"Channel URL: {metadata['channel_url']}")
        except TranscriptError as e:
            log_message(log_file, f"Error fetching metadata: {e}")
        
        # Get and display video statistics
        log_message(log_file, "\n--- Video Statistics ---")
        try:
            stats = get_video_statistics(video_id)
            if stats['views']:
                log_message(log_file, f"View count: {stats['views']}")
            else:
                log_message(log_file, "View count: Not available")
                
            if stats['likes']:
                log_message(log_file, f"Likes: {stats['likes']}")
            else:
                log_message(log_file, "Likes: Not available")
                
            if stats['upload_date']:
                log_message(log_file, f"Upload date: {stats['upload_date']}")
            else:
                log_message(log_file, "Upload date: Not available")
        except Exception as e:
            log_message(log_file, f"Error fetching statistics: {e}")
        
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