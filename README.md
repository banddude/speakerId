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

## Requirements

- Python 3.8+
- NeMo (NVIDIA Neural Modules)
- Pinecone (vector database)
- AssemblyAI API (for transcription)
- PyDub (for audio manipulation)

## Core Components

### Main Scripts

- `speaker_id_testing.py`: Main script to process conversations
- `update_speaker_db_verified.py`: Add verified utterances to the database
- `rename_speaker.py`: Rename speakers and update all related files
- `direct_model_download.py`: Download the TitaNet model

### Workflow

1. Process a conversation: `python speaker_id_testing.py your_audio_file.m4a`
2. Review and rename speakers if needed: `python rename_speaker.py conversation_path old_name new_name --update-db`
3. Optionally add more utterances: `python update_speaker_db_verified.py speaker_utterances/Speaker_Name --avg-confidence 0.60`

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - `ASSEMBLYAI_API_KEY`: Your AssemblyAI API key
   - `PINECONE_API_KEY`: Your Pinecone API key
4. Run `python direct_model_download.py` to download the TitaNet model
5. Create a Pinecone index named "speaker-embeddings"

## Notes

- Media files, model files, and processed conversations are not included in this repository
- You'll need to create your own `.env` file with your API keys
- First-time setup requires downloading the TitaNet model (~1GB) 