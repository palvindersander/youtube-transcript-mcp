#!/usr/bin/env python3
"""
Test script for the YouTube transcript fact-checking features.
Usage: python3 test_fact_checking.py <youtube_url_or_id> <claim> [test_type]
"""

import sys
import json
import os
import datetime
import asyncio
from typing import Dict, Any, Optional

import transcript_lib as tlib
import transcript_segment
import search_api

def print_usage():
    print("Usage: python3 test_fact_checking.py <youtube_url_or_id> <claim> [test_type]")
    print("Example: python3 test_fact_checking.py https://www.youtube.com/watch?v=ELj2LLNP8Ak \"AI will replace all jobs by 2025\"")
    print("Example: python3 test_fact_checking.py ELj2LLNP8Ak \"AI will replace all jobs by 2025\" segment")
    print("Example: python3 test_fact_checking.py ELj2LLNP8Ak \"AI will replace all jobs by 2025\" search")
    print("\nTest types:")
    print("  all     - Run all tests (default)")
    print("  segment - Test transcript segment extraction")
    print("  search  - Test search for claim verification")
    print("  find    - Test finding claim in transcript")

def log_message(log_file, message):
    """Write message to both console and log file."""
    print(message)
    if log_file:
        log_file.write(message + "\n")

async def test_search_for_claim(claim: str, context: str, log_file=None):
    """Test search for claim verification."""
    log_message(log_file, f"\n=== Testing Search for Claim Verification ===")
    log_message(log_file, f"Claim: {claim}")
    if context:
        log_message(log_file, f"Context: {context}")
    
    try:
        # Check if API key is configured
        api_key = os.environ.get("SEARCH_API_KEY")
        if not api_key:
            log_message(log_file, "Error: No SEARCH_API_KEY environment variable set.")
            log_message(log_file, "Please set this variable to your search API key to test search functionality.")
            return
        
        # Create search client and search for claim
        client = search_api.create_search_client(api_key)
        results = await client.search_for_claim_verification(claim, context)
        
        # Log number of results found
        fact_check_count = len(results.get("fact_check_results", {}).get("results", []))
        info_count = len(results.get("information_results", {}).get("results", []))
        
        log_message(log_file, f"Found {fact_check_count} fact-check results and {info_count} information results.")
        
        # Log top result from each search
        if fact_check_count > 0:
            top_result = results["fact_check_results"]["results"][0]
            log_message(log_file, "\nTop fact-check result:")
            log_message(log_file, f"Title: {top_result.get('title')}")
            log_message(log_file, f"Source: {top_result.get('source')}")
            log_message(log_file, f"Snippet: {top_result.get('snippet')}")
            log_message(log_file, f"Link: {top_result.get('link')}")
        
        if info_count > 0:
            top_result = results["information_results"]["results"][0]
            log_message(log_file, "\nTop information result:")
            log_message(log_file, f"Title: {top_result.get('title')}")
            log_message(log_file, f"Source: {top_result.get('source')}")
            log_message(log_file, f"Snippet: {top_result.get('snippet')}")
            log_message(log_file, f"Link: {top_result.get('link')}")
        
        # Save full results to JSON file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("logs", exist_ok=True)
        json_path = f"logs/search_results_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        log_message(log_file, f"\nFull results saved to {json_path}")
        
    except Exception as e:
        log_message(log_file, f"Error testing search: {str(e)}")

def test_extract_transcript_segment(url: str, timestamp: str, log_file=None):
    """Test extracting a segment from a transcript."""
    log_message(log_file, f"\n=== Testing Transcript Segment Extraction ===")
    log_message(log_file, f"URL: {url}")
    log_message(log_file, f"Timestamp: {timestamp}")
    
    try:
        # Extract the segment
        segment_data = transcript_segment.extract_transcript_segment(url, timestamp)
        
        # Display metadata
        log_message(log_file, f"\nVideo: {segment_data['video_title']}")
        log_message(log_file, f"Author: {segment_data['author']}")
        
        if segment_data['chapter']:
            log_message(log_file, f"Chapter: {segment_data['chapter']}")
        
        # Display the segment
        log_message(log_file, f"\nTranscript segment at {timestamp}:")
        log_message(log_file, "------------------------")
        log_message(log_file, segment_data['segment'])
        
    except Exception as e:
        log_message(log_file, f"Error extracting transcript segment: {str(e)}")

def test_find_claim_in_transcript(url: str, claim: str, log_file=None):
    """Test finding a claim in a transcript."""
    log_message(log_file, f"\n=== Testing Find Claim in Transcript ===")
    log_message(log_file, f"URL: {url}")
    log_message(log_file, f"Claim: {claim}")
    
    try:
        # Extract video ID
        video_id = tlib.get_video_id(url)
        
        # Get transcript
        transcript = tlib.get_transcript(video_id)
        
        # Try exact match first
        log_message(log_file, "\nTrying exact match...")
        result = transcript_segment.find_claim_in_transcript(transcript, claim, False)
        
        if result:
            log_message(log_file, f"Found exact match at timestamp: {result['timestamp']}")
            log_message(log_file, f"Context: {result['context']}")
        else:
            log_message(log_file, "No exact match found, trying fuzzy match...")
            result = transcript_segment.find_claim_in_transcript(transcript, claim, True)
            
            if result:
                log_message(log_file, f"Found fuzzy match at timestamp: {result['timestamp']}")
                log_message(log_file, f"Match confidence: {int(result['match_score'] * 100)}%")
                log_message(log_file, f"Context: {result['context']}")
                
                # Get surrounding transcript
                segment_data = transcript_segment.extract_transcript_segment(
                    url, result['timestamp'], 30
                )
                
                log_message(log_file, "\nSurrounding transcript:")
                log_message(log_file, "------------------------")
                log_message(log_file, segment_data['segment'])
            else:
                log_message(log_file, "Claim not found in transcript, even with fuzzy matching.")
    
    except Exception as e:
        log_message(log_file, f"Error finding claim: {str(e)}")

async def main():
    # Check arguments
    if len(sys.argv) < 3:
        print_usage()
        return 1
    
    url = sys.argv[1]
    claim = sys.argv[2]
    test_type = sys.argv[3].lower() if len(sys.argv) > 3 else "all"
    
    # Validate test type
    valid_test_types = ["all", "segment", "search", "find"]
    if test_type not in valid_test_types:
        print(f"Invalid test type: {test_type}")
        print_usage()
        return 1
    
    # Create log file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs", exist_ok=True)
    log_path = f"logs/fact_check_test_{timestamp}.log"
    
    try:
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_message(log_file, f"YouTube Fact Check Test - {datetime.datetime.now()}")
            log_message(log_file, f"URL: {url}")
            log_message(log_file, f"Claim: {claim}")
            log_message(log_file, f"Test type: {test_type}")
            
            # Get video metadata
            try:
                video_id = tlib.get_video_id(url)
                metadata = tlib.get_video_metadata(video_id)
                
                log_message(log_file, f"\n--- Video Information ---")
                log_message(log_file, f"Title: {metadata['title']}")
                log_message(log_file, f"Author: {metadata['author']}")
            except Exception as e:
                log_message(log_file, f"Error getting video metadata: {str(e)}")
            
            # Extract a timestamp for segment testing (middle of video) if needed
            timestamp = "0:30"  # Default
            if test_type in ["all", "segment"]:
                try:
                    transcript = tlib.get_transcript(video_id)
                    if transcript:
                        # Get a timestamp in middle of video
                        middle_index = len(transcript) // 2
                        middle_time = int(transcript[middle_index]['start'])
                        timestamp = transcript_segment.seconds_to_timestamp(middle_time)
                except Exception:
                    # Use default timestamp
                    pass
            
            # Run requested tests
            if test_type in ["all", "segment"]:
                test_extract_transcript_segment(url, timestamp, log_file)
                
            if test_type in ["all", "find"]:
                test_find_claim_in_transcript(url, claim, log_file)
                
            if test_type in ["all", "search"]:
                # Extract some context for the search
                context = None
                try:
                    metadata = tlib.get_video_metadata(video_id)
                    context = metadata['title']
                except Exception:
                    pass
                
                await test_search_for_claim(claim, context, log_file)
            
            log_message(log_file, f"\nTest completed. Results saved to {log_path}")
            return 0
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    asyncio.run(main()) 