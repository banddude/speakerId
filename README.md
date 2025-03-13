# Speaker Identification System

A complete end-to-end speaker identification system for audio conversations, featuring:

- Automatic transcription with speaker diarization
- Speaker identification using neural embeddings
- Short utterance handling
- Self-improving database
- Conversation management and organization

## Features

- **Conversation Processing**: Transcribe and analyze audio files with speaker diarization
- **Speaker Identification**: Match speakers to a database of voice embeddings using NeMo TitaNet
- **Short Utterance Handling**: Special handling for very short utterances, combining utterances when needed
- **Self-improving Database**: Automatically adds high-quality utterances to improve future recognition
- **Complete Organization**: Structured storage of conversations, utterances, and metadata
- **Rename Functionality**: Tools to rename speakers and update all related files

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Audio Input    │────▶│  Transcription  │────▶│  Speaker ID     │
│  (.m4a, .wav)   │     │  (AssemblyAI)   │     │  (NeMo TitaNet) │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Frontend UI    │◀───▶│  Speaker DB     │◀────│  Conversation   │
│  (Web/Mobile)   │     │  (Pinecone)     │     │  Metadata       │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Core Scripts and Front-End Integration

### Main Scripts

1. **speaker_id_testing.py**: Main script to process conversations
   - **Input**: Audio file path
   - **Output**: Processed conversation with metadata, transcript, and utterances
   - **Front-End Usage**: Call via API to process new audio files
   - **Format**: Returns JSON metadata with conversation details

2. **update_speaker_db_verified.py**: Add verified utterances to the database
   - **Input**: Speaker directory path, confidence threshold
   - **Output**: Updates Pinecone database with new voice embeddings
   - **Front-End Usage**: Call to add new speaker samples or improve existing ones

3. **rename_speaker.py**: Rename speakers and update all related files
   - **Input**: Conversation path, old speaker name, new speaker name
   - **Output**: Updated files with the new speaker name
   - **Front-End Usage**: Call to correct misidentified speakers

4. **direct_model_download.py**: Download the TitaNet model
   - **Input**: None
   - **Output**: Downloaded model to models directory
   - **Front-End Usage**: Call during initial setup or model updates

### Data Structures

#### Conversation Metadata (JSON)

```json
{
  "conversation_id": "conversation_20250312_161957",
  "original_audio": "original_audio.m4a",
  "date_processed": "2025-03-12T16:19:57.123456",
  "duration_seconds": 360.5,
  "speakers": ["Mike Shaffer", "Simeon Reyes"],
  "utterances": [
    {
      "id": "utterance_001",
      "start_time": "00:00:05",
      "end_time": "00:00:10",
      "start_ms": 5000,
      "end_ms": 10000,
      "speaker": "Mike Shaffer",
      "text": "Hello, how are you?",
      "confidence": 0.85,
      "embedding_id": "speaker_Mike_Shaffer_abc123",
      "audio_file": "utterances/utterance_001.wav"
    },
    // More utterances...
  ],
  "short_utterance_stats": {
    "total": 14,
    "identified_directly": 12,
    "identified_combined": 2,
    "unidentified": 0
  },
  "database_update_stats": {
    "added": 5,
    "skipped_low_confidence": 2,
    "skipped_unknown": 1,
    "skipped_duplicate": 6
  }
}
```

#### Speaker Database Structure (Pinecone)

Each vector in Pinecone has:
- **ID**: Unique identifier (e.g., "speaker_Mike_Shaffer_abc123")
- **Vector**: 192-dimensional voice embedding from TitaNet
- **Metadata**:
  - `speaker_name`: Name of the speaker
  - `source_file`: Source audio file
  - `is_short_utterance`: Whether this is a short utterance
  - `duration_seconds`: Duration of the utterance

## Front-End Development Guide

### Suggested Features

1. **Conversation Management**
   - Upload and process new audio files
   - List all processed conversations
   - View conversation details, transcripts, and utterances
   - Visualize speaker timeline and participation

2. **Speaker Management**
   - List all speakers in the database
   - View speaker details and statistics
   - Add new speakers
   - Rename speakers
   - Add utterances to improve speaker recognition

3. **Transcript Visualization**
   - Interactive transcript with speaker highlighting
   - Timeline view of speaker contributions
   - Search functionality for transcript content
   - Export options (JSON, TXT, SRT)

4. **Database Management**
   - View database statistics
   - Manage voice embeddings (add, remove)
   - Adjust confidence thresholds
   - Backup/restore functionality

### REST API Endpoints (To Be Implemented)

For a full frontend, you would want to implement these API endpoints:

```
GET /api/conversations - List all conversations
GET /api/conversations/{id} - Get conversation details
POST /api/conversations - Upload and process a new conversation
DELETE /api/conversations/{id} - Delete a conversation

GET /api/speakers - List all speakers
GET /api/speakers/{id} - Get speaker details
POST /api/speakers - Add a new speaker
PUT /api/speakers/{id} - Update speaker (rename)
DELETE /api/speakers/{id} - Delete a speaker

POST /api/utterances - Add an utterance to the database
GET /api/utterances/{speaker_id} - Get utterances for a speaker
DELETE /api/utterances/{id} - Delete an utterance
```

### Integration Steps

1. **Create a Python Flask/FastAPI Backend**
   - Wrap existing scripts in API endpoints
   - Handle file uploads and processing
   - Manage authentication and permissions
   - Implement caching for better performance

2. **Build a Modern Frontend**
   - Use React, Vue, or Angular for the UI
   - Implement responsive design for mobile/desktop
   - Create interactive visualizations for transcripts
   - Design an intuitive speaker management interface

3. **Real-time Processing**
   - Implement WebSockets for real-time processing updates
   - Show progress during long-running operations
   - Provide notification system for completed processes

4. **Deployment Considerations**
   - CPU/GPU requirements for the NeMo model
   - Storage for audio files and processed conversations
   - API rate limits for AssemblyAI and Pinecone
   - Authentication and authorization

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - `ASSEMBLYAI_API_KEY`: Your AssemblyAI API key
   - `PINECONE_API_KEY`: Your Pinecone API key
4. Run `python direct_model_download.py` to download the TitaNet model
5. Create a Pinecone index named "speaker-embeddings"

## Directory Structure

```
speaker-identification/
├── models/                  # Downloaded NeMo models
├── processed_conversations/ # Organized conversation data
│   └── conversation_id/
│       ├── metadata.json    # Conversation metadata
│       ├── transcript.txt   # Formatted transcript
│       ├── original_audio.* # Original audio file
│       ├── utterances/      # Individual audio segments
│       └── speakers/        # Utterances organized by speaker
├── speaker_utterances/      # Legacy storage for utterances
├── hf_cache/                # HuggingFace cache directory
├── *.py                     # Python scripts
└── requirements.txt         # Dependencies
```

## Notes

- This repository includes conversation metadata but excludes audio files
- You'll need to create your own `.env` file with your API keys
- First-time setup requires downloading the TitaNet model (~1GB)
- For production use, consider implementing a proper REST API layer 