# YouTube Transcript MCP Documentation

Welcome to the documentation for the YouTube Transcript MCP server. This project provides an MCP (Machine-Callable Program) service for fetching and processing YouTube video transcripts, making them available to Claude and other applications.

## Documentation Index

### Getting Started
- [README](../README.md) - Overview, installation, and usage instructions

### Project Status
- [Progress Tracker](progress_tracker.md) - Current status, completed features, and roadmap
- [Project Updates](project_updates.md) - Major architectural changes and development history

### Technical Documentation
- [Developer Guide](developer_guide.md) - Comprehensive guide for developers working on the codebase
- [Fact-Checking Design](fact_checking_design.md) - Design document for the fact-checking feature

### Files and Components

#### Core Files
- `transcript_lib.py` - Core library with transcript processing functionality
- `transcript_mcp.py` - MCP server implementation exposing tools to Claude
- `transcript_segment.py` - Transcript segment extraction for fact-checking
- `search_api.py` - Web search client for fact verification

#### Test Scripts
- `test_transcript.py` - Test script for transcript functionality
- `test_chapter_markers.py` - Test script for chapter markers extraction
- `test_statistics.py` - Test script for video statistics extraction
- `test_fact_checking.py` - Test script for fact-checking features

#### Configuration
- `requirements.txt` - Python package dependencies
- `.gitignore` - Git ignore file

#### Output
- `logs/` - Directory for log files with transcript results

## Core Features

- **Transcript Retrieval**: Fetch and format transcripts from YouTube videos
- **Chapter Markers**: Extract and display chapter markers within transcripts
- **Video Metadata**: Retrieve comprehensive video information
- **Video Statistics**: Extract view counts, likes, and upload dates
- **Language Support**: Access transcripts in multiple languages
- **Fact-Checking**: Tools to help Claude verify claims from video content

## Retired Features

For information about features that were implemented but later removed, see the [Project Updates](project_updates.md#feature-speaker-identification-implemented--later-removed) document and the [Retired Features](progress_tracker.md#retired-features) section in the Progress Tracker.

## Getting Started

To get started with using or developing the YouTube Transcript MCP server, follow these steps:

1. Read the [README](../README.md) for installation and setup instructions
2. Check the [Progress Tracker](progress_tracker.md) to understand the current state of the project
3. For development, refer to the [Developer Guide](developer_guide.md)
4. Review [Project Updates](project_updates.md) to understand architectural decisions

## Project Vision

The YouTube Transcript MCP server aims to provide a bridge between YouTube's transcript data and Claude, enabling rich conversational interactions around video content. Future enhancements will focus on adding richer transcript processing, additional metadata, and advanced analysis capabilities.

## Current Capabilities

- Fetch transcripts from any YouTube video with captions
- Merge transcript segments into readable chunks with timestamps
- Extract video metadata (title, author, description) and statistics
- Include chapter markers in transcripts for better navigation
- Support for multiple languages
- MCP integration with Claude Desktop
- Search for information to verify claims from videos
- Extract specific transcript segments for focused analysis
- Find claims within transcripts and provide context
- Comprehensive logging and testing tools

## Recent Updates

- Added fact-checking tools to help Claude verify claims from videos
- Enhanced search integration for finding verification information
- Added transcript segment extraction for focused analysis
- Removed speaker identification functionality due to limited effectiveness
- Added comprehensive documentation about architectural decisions
- Simplified codebase by focusing on core functionality
- Improved project documentation organization

For more detailed information about recent changes, see the [Recent Updates](progress_tracker.md#recent-updates) section in the Progress Tracker. 