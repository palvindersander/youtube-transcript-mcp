#!/usr/bin/env python3
"""
Test script for speaker identification using sample data.
This demonstrates how the speaker identification works without requiring a specific YouTube video.
"""

import json
import sys
from transcript_lib import identify_speakers, format_transcript_with_speakers

# Sample transcript data with speaker labels embedded in the text
sample_transcript = [
    {
        "text": "John: Welcome to our discussion on artificial intelligence.",
        "start": 0.0,
        "duration": 3.5
    },
    {
        "text": "Sarah: Thanks for having me, John. I'm excited to be here.",
        "start": 3.5,
        "duration": 4.2
    },
    {
        "text": "John: Let's start by talking about recent advancements.",
        "start": 7.7,
        "duration": 3.8
    },
    {
        "text": "Sarah: Well, there's been significant progress in large language models.",
        "start": 11.5,
        "duration": 5.0
    },
    {
        "text": "This has led to systems that can understand and generate human-like text.",
        "start": 16.5,
        "duration": 4.8
    },
    {
        "text": "John: That's fascinating. How are these being applied?",
        "start": 21.3,
        "duration": 3.2
    },
    {
        "text": "Sarah: They're being used in customer service, content creation, and coding assistance.",
        "start": 24.5,
        "duration": 5.5
    },
    {
        "text": "Interviewer: What about ethical considerations?",
        "start": 30.0,
        "duration": 2.8
    },
    {
        "text": "Sarah: Great question. We need to address bias and ensure transparency.",
        "start": 32.8,
        "duration": 4.7
    },
    {
        "text": "[John] And what about privacy concerns?",
        "start": 37.5,
        "duration": 2.5
    },
    {
        "text": "(Sarah) Those are equally important. We must ensure data protection.",
        "start": 40.0,
        "duration": 4.0
    },
    {
        "text": "This is especially true when handling sensitive information.",
        "start": 44.0,
        "duration": 3.5
    },
    {
        "text": "Host: Thank you both for this enlightening discussion.",
        "start": 47.5,
        "duration": 3.0
    }
]

def main():
    print("===== Speaker Identification Test with Sample Data =====\n")
    
    # Identify speakers in the sample transcript
    print("Identifying speakers in sample transcript...")
    transcript_with_speakers, speakers = identify_speakers(sample_transcript)
    
    # Report on identified speakers
    if speakers:
        print(f"\nFound {len(speakers)} potential speakers:")
        for speaker, occurrences in speakers.items():
            print(f"- {speaker}: {len(occurrences)} occurrences")
    else:
        print("\nNo speakers identified using pattern matching.")
    
    # Format and display transcript with speakers
    print("\nTranscript with speakers:")
    print("------------------------")
    formatted_transcript = format_transcript_with_speakers(transcript_with_speakers)
    print(formatted_transcript)
    
    # Show raw JSON with speaker labels
    print("\nRaw Transcript Data with Speakers (JSON):")
    print("----------------------------------------")
    print(json.dumps(transcript_with_speakers[:3], indent=2))
    print("... (truncated)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 