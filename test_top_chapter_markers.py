#!/usr/bin/env python3

import sys
import os
import json
import datetime
from typing import Dict, Any, Optional
import transcript_lib as tlib

def test_top_chapter_markers(video_id: str, language_code: Optional[str] = None):
    """Test the display of chapter markers at the top of transcript output.
    
    Args:
        video_id: YouTube video ID to test with
        language_code: Optional language code to test with
    """
    print(f"Testing chapter markers at top for video {video_id}")
    print("=" * 80)
    
    try:
        # Create a mock result similar to what the MCP server would do
        result = ""
        
        # Add metadata
        try:
            metadata = tlib.get_video_metadata(video_id)
            stats = tlib.get_video_statistics(video_id)
            
            result += f"--- Video Metadata ---\n"
            result += f"Title: {metadata['title']}\n"
            result += f"Author: {metadata['author']}\n"
            result += f"Channel URL: {metadata['channel_url']}\n"
            
            if stats:
                if stats.get('views'):
                    result += f"Views: {stats['views']}\n"
                if stats.get('likes'):
                    result += f"Likes: {stats['likes']}\n"
                if stats.get('upload_date'):
                    result += f"Upload date: {stats['upload_date']}\n"
            
            result += "\n"
        except Exception as e:
            result += f"Error fetching metadata: {str(e)}\n\n"
        
        # Get chapters and add them at the top
        chapters = None
        try:
            chapters = tlib.get_chapter_markers(video_id)
            
            # Add chapter markers at the top (new feature being tested)
            if chapters:
                result += f"--- Chapter Markers ---\n"
                for chapter in chapters:
                    result += f"[{chapter['start_time_formatted']}] {chapter['title']}\n"
                result += "\n"
            else:
                result += "No chapter markers found for this video.\n\n"
        except Exception as e:
            result += f"Error fetching chapter markers: {str(e)}\n\n"
        
        # Get transcript
        transcript = tlib.get_transcript(video_id, language_code)
        
        # Format with timestamps and include chapters inline as well
        result += tlib.format_transcript_text(transcript, chapters)
        
        # Print the result
        print(result)
        
        # Save to log file
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{log_dir}/test_top_chapter_markers_{timestamp}.txt"
        
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(result)
        
        print(f"\nLog saved to {log_filename}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Use the video ID provided as command line argument,
    # or default to a video known to have chapters
    video_id = sys.argv[1] if len(sys.argv) > 1 else "ELj2LLNP8Ak"
    
    # Optional language code
    language_code = sys.argv[2] if len(sys.argv) > 2 else None
    
    test_top_chapter_markers(video_id, language_code) 