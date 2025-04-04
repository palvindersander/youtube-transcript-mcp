#!/usr/bin/env python3
"""
Transcript segment extraction utilities for fact-checking.
This module provides functionality to extract specific segments
from YouTube transcripts based on timestamps or content.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import transcript_lib as tlib

def timestamp_to_seconds(timestamp: str) -> int:
    """Convert a timestamp string to seconds.
    
    Args:
        timestamp: Timestamp string in format MM:SS or HH:MM:SS
        
    Returns:
        Time in seconds
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    # Check format and parse
    if re.match(r'^\d+:\d{2}$', timestamp):  # MM:SS
        minutes, seconds = timestamp.split(':')
        return int(minutes) * 60 + int(seconds)
    elif re.match(r'^\d+:\d{2}:\d{2}$', timestamp):  # HH:MM:SS
        hours, minutes, seconds = timestamp.split(':')
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}. Expected MM:SS or HH:MM:SS")

def seconds_to_timestamp(seconds: int) -> str:
    """Convert seconds to a timestamp string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string (MM:SS or HH:MM:SS)
    """
    if seconds < 3600:
        # Format as MM:SS
        minutes = seconds // 60
        seconds_remainder = seconds % 60
        return f"{minutes:01d}:{seconds_remainder:02d}"
    else:
        # Format as HH:MM:SS
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds_remainder = seconds % 60
        return f"{hours:01d}:{minutes:02d}:{seconds_remainder:02d}"

def find_transcript_segment(transcript: List[Dict], target_time: int, context_seconds: int = 30) -> List[Dict]:
    """Find a segment of transcript around a specific time.
    
    Args:
        transcript: Full transcript data
        target_time: Target time in seconds
        context_seconds: Number of seconds of context to include before and after
        
    Returns:
        List of transcript segments around the target time
    """
    # Calculate time range
    start_time = max(0, target_time - context_seconds)
    end_time = target_time + context_seconds
    
    # Find segments within range
    segment = []
    for item in transcript:
        item_start = item['start']
        item_end = item_start + item.get('duration', 0)
        
        if (item_start >= start_time and item_start <= end_time) or \
           (item_end >= start_time and item_end <= end_time) or \
           (item_start <= start_time and item_end >= end_time):
            segment.append(item)
    
    return segment

def extract_transcript_segment(url: str, timestamp: str, context_seconds: int = 30, 
                               language_code: Optional[str] = None) -> Dict[str, Any]:
    """Extract a specific segment of a transcript around a timestamp.
    
    Args:
        url: YouTube video URL or ID
        timestamp: Timestamp in format MM:SS or HH:MM:SS
        context_seconds: Number of seconds of context before and after
        language_code: Optional language code for the transcript
        
    Returns:
        Dict containing the transcript segment with metadata
        
    Raises:
        tlib.TranscriptError: If transcript cannot be retrieved
        ValueError: If timestamp format is invalid
    """
    # Extract video ID from URL
    video_id = tlib.get_video_id(url)
    
    # Convert timestamp to seconds
    target_time = timestamp_to_seconds(timestamp)
    
    # Get the full transcript
    transcript = tlib.get_transcript(video_id, language_code)
    
    # Extract relevant segment
    segment = find_transcript_segment(transcript, target_time, context_seconds)
    
    # Get video metadata
    try:
        metadata = tlib.get_video_metadata(video_id)
    except:
        metadata = {"title": "Unknown", "author": "Unknown"}
    
    # Get chapter information if available
    try:
        chapters = tlib.get_chapter_markers(video_id)
        current_chapter = None
        
        if chapters:
            # Find which chapter the timestamp is in
            for chapter in chapters:
                chapter_start = timestamp_to_seconds(chapter['start_time_formatted'])
                if chapter_start <= target_time:
                    current_chapter = chapter
    except:
        chapters = None
        current_chapter = None
    
    # Format the segment
    formatted_segment = tlib.format_transcript_text(segment)
    
    # Prepare the response
    result = {
        "video_id": video_id,
        "video_title": metadata.get("title", "Unknown"),
        "author": metadata.get("author", "Unknown"),
        "timestamp": timestamp,
        "timestamp_seconds": target_time,
        "context_seconds": context_seconds,
        "chapter": current_chapter["title"] if current_chapter else None,
        "segment": formatted_segment
    }
    
    return result

def find_claim_in_transcript(transcript: List[Dict], claim: str, 
                           fuzzy_match: bool = True) -> Optional[Dict]:
    """Find a specific claim in the transcript and return its timestamp.
    
    Args:
        transcript: Full transcript data
        claim: The claim to find
        fuzzy_match: Whether to use fuzzy matching (more lenient)
        
    Returns:
        Dict with timestamp and context if found, None otherwise
    """
    # Normalize claim for comparison
    normalized_claim = claim.lower().strip()
    
    # For exact matching
    for item in transcript:
        text = item['text'].lower()
        if normalized_claim in text:
            return {
                'timestamp': seconds_to_timestamp(int(item['start'])),
                'timestamp_seconds': int(item['start']),
                'context': item['text']
            }
    
    # If no exact match and fuzzy matching is enabled
    if fuzzy_match:
        # Try word-by-word matching (find where most words match)
        claim_words = set(normalized_claim.split())
        best_match = None
        best_match_score = 0
        
        for item in transcript:
            text = item['text'].lower()
            text_words = set(text.split())
            
            # Calculate overlap
            common_words = claim_words.intersection(text_words)
            match_score = len(common_words) / len(claim_words)
            
            if match_score > 0.5 and match_score > best_match_score:
                best_match = item
                best_match_score = match_score
        
        if best_match:
            return {
                'timestamp': seconds_to_timestamp(int(best_match['start'])),
                'timestamp_seconds': int(best_match['start']),
                'context': best_match['text'],
                'match_score': best_match_score
            }
    
    return None 