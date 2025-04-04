#!/usr/bin/env python3
"""
Test script for fetching YouTube video metadata.
Usage: python3 test_metadata.py <youtube_url_or_id> [log_file]
"""

import sys
import json
import re
import os
import datetime
import requests
from transcript_lib import get_video_id

def get_video_metadata(video_id: str) -> dict:
    """Fetch video metadata (title and description) using YouTube's oEmbed API.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary with title and description
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
        print(f"Error fetching title from oEmbed: {e}")
    
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
        print(f"Error fetching description: {e}")
    
    return metadata

def log_message(log_file, message):
    """Write message to both console and log file."""
    print(message)
    if log_file:
        log_file.write(message + "\n")

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python3 test_metadata.py <youtube_url_or_id> [log_file]")
        return 1
    
    url = sys.argv[1]
    
    # Default log file is logs/metadata_<video_id>_<timestamp>.log
    log_path = None
    if len(sys.argv) > 2:
        log_path = sys.argv[2]
    
    log_file = None
    
    try:
        # Extract video ID from URL
        video_id = get_video_id(url)
        
        # Create log file if not specified
        if not log_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)
            log_path = f"logs/metadata_{video_id}_{timestamp}.log"
        
        # Open log file
        log_file = open(log_path, "w", encoding="utf-8")
        
        log_message(log_file, f"YouTube Metadata Test - {datetime.datetime.now()}")
        log_message(log_file, f"Video ID: {video_id}")
        log_message(log_file, f"URL: {url}")
        
        # Get metadata
        log_message(log_file, "\nFetching video metadata...")
        metadata = get_video_metadata(video_id)
        
        # Display results
        log_message(log_file, "\n--- Video Metadata ---")
        log_message(log_file, f"Title: {metadata['title']}")
        log_message(log_file, f"Author: {metadata['author']}")
        log_message(log_file, f"Channel URL: {metadata['channel_url']}")
        log_message(log_file, f"Thumbnail URL: {metadata['thumbnail_url']}")
        log_message(log_file, "\nDescription:")
        log_message(log_file, "-------------")
        log_message(log_file, metadata['description'])
        
        # Write raw metadata as JSON
        log_message(log_file, "\nRaw Metadata (JSON):")
        log_message(log_file, "-------------------")
        log_file.write(json.dumps(metadata, indent=2) + "\n")
        
        log_message(log_file, f"\nResults saved to {log_path}")
        return 0
    
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