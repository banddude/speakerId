# Speaker Identification Backend

This Flask-based backend provides API endpoints for the Speaker Identification System. It connects the Next.js frontend with the underlying Python scripts for speaker identification, conversation processing, and database management.

## Features

- REST API for conversation management
- Audio file processing
- Speaker identification
- Utterance management
- Background processing of audio files

## API Endpoints

### Conversations

- `GET /api/conversations` - Get all conversations
- `GET /api/conversations/:id` - Get a specific conversation

### Speakers

- `GET /api/speakers` - Get all speakers
- `POST /api/speakers/rename` - Rename a speaker

### Audio Processing

- `POST /api/process` - Upload and process an audio file
- `GET /api/process/:id` - Get processing status

### Audio Files

- `GET /api/audio/:id` - Get full conversation audio
- `GET /api/audio/:id/segments/:segmentId` - Get segment audio

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the server:
   ```
   python app.py
   ```

## Integration with Frontend

The backend serves API endpoints that match what the frontend expects. To connect them:

1. Start the backend server (port 5000 by default)
2. Configure the frontend to point to the backend API:
   - Set `NEXT_PUBLIC_API_URL=http://localhost:5000/api` in `.env.local`
3. Start the frontend (port 3000 by default)

Or use the provided script to run both simultaneously:
```
./run_app.sh
```

## Background Processing

Audio processing happens in background threads to avoid blocking the API:

1. When a file is uploaded, it's saved to the `uploads` directory
2. A background thread processes the file using the speaker identification system
3. The client can poll the status endpoint to check progress
4. Once processing is complete, the conversation is available through the API

## Development

To modify or extend the backend:

- Add new endpoints in `app.py`
- Create new utility functions in the `utils` folder
- Update models in the `models` folder 