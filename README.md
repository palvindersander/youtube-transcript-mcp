# YouTube Transcript MCP Server

An MCP server for fetching transcripts from YouTube videos directly in Claude.

> **Documentation**: For complete documentation, see the [Documentation Index](docs/index.md).

## Architecture

### System Overview

```mermaid
graph TD
    Claude[Claude Desktop] -->|Command| MCP[MCP Protocol]
    MCP -->|Request| Server[Transcript MCP Server]
    Server -->|Parse URL| YTLib[Transcript Library]
    YTLib -->|Extract Video ID| YT[YouTube]
    YTLib -->|Fetch Transcript| YT
    YTLib -->|Fetch Metadata| YT
    YTLib -->|Process| Results[Results]
    Results -->|Format Response| Server
    Server -->|Return Data| MCP
    MCP -->|Display Results| Claude
    
    subgraph "Transcript Server"
        Server
        YTLib
    end
    
    subgraph "External Services"
        YT
    end
    
    subgraph "Client"
        Claude
        MCP
    end
```

### Component Structure

```mermaid
classDiagram
    class FastMCP {
        +run()
        +tool()
    }
    
    class TranscriptMCPServer {
        +get_transcript()
        +get_video_metadata()
        +list_transcript_languages()
        +get_chapter_markers()
    }
    
    class TranscriptLib {
        +get_video_id()
        +get_video_metadata()
        +get_video_statistics()
        +get_available_languages()
        +get_transcript()
        +get_chapter_markers()
        +format_transcript_text()
        +format_transcript_json()
    }
    
    class YouTubeTranscriptAPI {
        +get_transcript()
        +list_transcripts()
    }
    
    class TranscriptError {
        +message
    }
    
    FastMCP <|-- TranscriptMCPServer : extends
    TranscriptMCPServer --> TranscriptLib : uses
    TranscriptLib --> YouTubeTranscriptAPI : uses
    TranscriptLib --> TranscriptError : throws
```

### Request Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Claude
    participant MCPServer
    participant TranscriptLib
    participant YouTube
    
    User->>Claude: @transcript get_transcript [URL]
    Claude->>MCPServer: Call get_transcript
    MCPServer->>TranscriptLib: get_video_id(url)
    MCPServer->>TranscriptLib: get_video_metadata(video_id)
    TranscriptLib->>YouTube: HTTP request to oEmbed API
    YouTube-->>TranscriptLib: Return metadata
    TranscriptLib->>YouTube: HTTP request to page
    YouTube-->>TranscriptLib: Return page content
    TranscriptLib-->>MCPServer: Return metadata
    
    MCPServer->>TranscriptLib: get_video_statistics(video_id)
    TranscriptLib->>YouTube: HTTP request to page
    YouTube-->>TranscriptLib: Return page content
    TranscriptLib-->>MCPServer: Return statistics
    
    MCPServer->>TranscriptLib: get_chapter_markers(video_id)
    TranscriptLib->>YouTube: HTTP request to page
    YouTube-->>TranscriptLib: Return page content
    TranscriptLib-->>MCPServer: Return chapter markers
    
    MCPServer->>TranscriptLib: get_transcript(video_id)
    TranscriptLib->>YouTube: Request transcript
    YouTube-->>TranscriptLib: Return raw transcript
    TranscriptLib-->>MCPServer: Return transcript segments
    MCPServer->>TranscriptLib: format_transcript_text(transcript, chapters)
    TranscriptLib-->>MCPServer: Return formatted transcript with chapters
    MCPServer-->>Claude: Return complete response
    Claude-->>User: Display transcript with metadata, statistics, and chapters
```

## Project Status and Roadmap

This project is actively maintained. For information about:
- Current implementation status
- Completed features
- Planned enhancements
- Roadmap for future development

See the [Progress Tracker](docs/progress_tracker.md).

## Setup Instructions

1. Install dependencies:
   ```
   python3 -m pip install -r requirements.txt
   ```

2. Configure Claude for Desktop:
   
   Open your Claude for Desktop App configuration at `~/Library/Application Support/Claude/claude_desktop_config.json` and add:
   
   ```json
   {
       "mcpServers": {
           "transcript": {
               "command": "python3",
               "args": [
                   "/absolute/path/to/transcript_mcp.py"
               ]
           }
       }
   }
   ```
   
   Make sure to replace `/absolute/path/to/transcript_mcp.py` with the actual path to the MCP script.

## Usage

Once configured, you can use the transcript MCP server in Claude with commands like:

```
@transcript get_transcript https://www.youtube.com/watch?v=ELj2LLNP8Ak
```

Or:

```
@transcript list_transcript_languages https://www.youtube.com/watch?v=ELj2LLNP8Ak
```

Or:

```
@transcript get_video_metadata https://www.youtube.com/watch?v=ELj2LLNP8Ak
```

## Available Tools

1. `get_transcript(url, language_code=None, include_metadata=True, include_chapters=True)`
   - Fetches a transcript for a YouTube video with timestamps in ~10 second intervals
   - Arguments:
     - `url`: YouTube video URL or ID
     - `language_code` (optional): Language code (e.g., 'en', 'es')
     - `include_metadata` (optional): Whether to include video metadata (default: True)
     - `include_chapters` (optional): Whether to include chapter markers in the transcript (default: True)
   - Returns:
     - Video metadata (title, author, channel URL, view count, etc.) if requested
     - Chapter markers if available and requested
     - Transcript with timestamps and chapter markers

2. `get_video_metadata(url, include_statistics=True)`
   - Fetches metadata and statistics for a YouTube video
   - Arguments:
     - `url`: YouTube video URL or ID
     - `include_statistics` (optional): Whether to include view count, likes, etc. (default: True)
   - Returns:
     - Video title
     - Author/channel name
     - Channel URL
     - Thumbnail URL
     - View count (if available)
     - Like count (if available)
     - Upload date (if available)
     - Video description

3. `list_transcript_languages(url)`
   - Lists available transcript languages for a YouTube video
   - Arguments:
     - `url`: YouTube video URL or ID

4. `get_chapter_markers(url)`
   - Fetches chapter markers for a YouTube video
   - Arguments:
     - `url`: YouTube video URL or ID
   - Returns:
     - List of chapter markers with timestamps and titles, or a message if no chapters are found

## Transcript Format

The transcript is formatted with timestamps in approximately 10-second intervals. Short segments are merged until they reach about 10 seconds in duration. Each line is prefixed with a timestamp in `[MM:SS]` format.

When chapter markers are available and included, they are displayed in two ways:
1. As a complete list at the top of the response under the "Chapter Markers" section
2. Inserted at appropriate positions in the transcript with a format like `[CHAPTER] MM:SS - Chapter Title`

This dual approach makes it easier to get an overview of the video structure while also seeing chapter transitions as you read through the content.

## Video Metadata and Statistics

The server can extract the following information from YouTube videos:
- Video title
- Author/channel name
- Channel URL
- Thumbnail URL
- View count
- Like count
- Upload date
- Video description

This information can be included with transcripts or retrieved separately using the `get_video_metadata` tool.

## Chapter Markers

Chapter markers are segments of a video defined by the video creator. The server can extract these markers from YouTube videos when available. Each chapter has:
- A title describing the content
- A timestamp indicating when the chapter starts
- A formatted time string (HH:MM:SS or MM:SS)

Chapter markers can be included directly in the transcript to provide additional context and structure, or retrieved separately using the `get_chapter_markers` tool.

## Testing

You can test the core functionality with the included test scripts:

```
python3 test_transcript.py [video_id] [language_code]
python3 test_chapter_markers.py [video_id]
python3 test_statistics.py [video_id]
python3 test_top_chapter_markers.py [video_id] [language_code]
```

Notes:
- Always run test scripts with `python3` rather than making them executable
- The `video_id` parameter can be a full YouTube URL or just the ID
- If no `video_id` is provided, a default testing video will be used
- Log files with timestamps are saved in the `logs/` directory

## Development Guidelines

When developing for this project:

1. Always run Python scripts using `python3` rather than making them executable
2. Test changes thoroughly with the provided test scripts
3. Document any significant changes in the appropriate documentation files
4. Follow the existing code style for consistency
