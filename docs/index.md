# YouTube Transcript MCP Documentation

Welcome to the documentation for the YouTube Transcript MCP server. This project provides an MCP (Machine-Callable Program) service for fetching and processing YouTube video transcripts, making them available to Claude and other applications.

## Documentation Index

### Getting Started
- [README](../README.md) - Overview, installation, and usage instructions

### Project Status
- [Progress Tracker](progress_tracker.md) - Current status, completed features, and roadmap

### Technical Documentation
- [Developer Guide](developer_guide.md) - Comprehensive guide for developers working on the codebase

### Files and Components

#### Core Files
- `transcript_lib.py` - Core library with transcript processing functionality
- `transcript_mcp.py` - MCP server implementation exposing tools to Claude
- `test_transcript.py` - Test script for transcript functionality
- `test_metadata.py` - Test script for metadata extraction

#### Configuration
- `requirements.txt` - Python package dependencies
- `.gitignore` - Git ignore file

#### Output
- `logs/` - Directory for log files with transcript results

## Getting Started

To get started with using or developing the YouTube Transcript MCP server, follow these steps:

1. Read the [README](../README.md) for installation and setup instructions
2. Check the [Progress Tracker](progress_tracker.md) to understand the current state of the project
3. For development, refer to the [Developer Guide](developer_guide.md)

## Project Vision

The YouTube Transcript MCP server aims to provide a bridge between YouTube's transcript data and Claude, enabling rich conversational interactions around video content. Future enhancements will focus on adding richer transcript processing, additional metadata, and advanced analysis capabilities.

## Key Features

- Fetch transcripts from any YouTube video with captions
- Merge transcript segments into readable chunks with timestamps
- Extract video metadata (title, author, description)
- Support for multiple languages
- MCP integration with Claude Desktop
- Comprehensive logging and testing tools 