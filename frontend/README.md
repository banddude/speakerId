Thought for 1 second### Speaker Identification System - Frontend

A Next.js frontend application for managing and interacting with a speaker identification system. This application provides a user interface for processing audio files, viewing transcriptions, managing speakers, and analyzing conversation data.

## Overview

This frontend application is designed to work with a Python-based speaker identification backend. It provides a complete user interface for:

- Uploading and processing audio files
- Viewing and searching conversation transcriptions
- Managing speaker identities
- Playing audio files and individual utterances
- Renaming and identifying unknown speakers


## Project Structure

```plaintext
speaker-identification/
├── app/                      # Next.js app router
│   ├── page.tsx              # Home/dashboard page
│   ├── conversation/         # Conversation viewer
│   │   └── [id]/page.tsx     # Individual conversation page
├── components/               # React components
│   ├── audio-player.tsx      # Audio playback component
│   ├── conversation-list.tsx # List of processed conversations
│   ├── process-audio.tsx     # Audio upload and processing
│   ├── rename-speaker-dialog.tsx # Dialog for renaming speakers
│   ├── speaker-stats.tsx     # Speaker database management
│   └── ui/                   # UI components (shadcn/ui)
├── lib/                      # Utility functions
│   ├── api-mock.ts           # Mock API functions (replace with real API)
│   ├── mock-data.ts          # Mock data for development
│   └── utils.ts              # Utility functions
├── types/                    # TypeScript type definitions
│   └── index.ts              # Data model type definitions
└── README.md                 # This file
```

## Installation

### Prerequisites

- Node.js 18.x or later
- npm or yarn
- Python 3.8+ (for the backend)


### Dependencies

This project uses the following main dependencies:

- **Next.js**: React framework
- **React**: UI library
- **TypeScript**: Type checking
- **Tailwind CSS**: Styling
- **Lucide React**: Icons
- **shadcn/ui**: UI components
- **class-variance-authority**: Styling utilities
- **clsx**: Class name utilities


### Setup Instructions

1. Clone the repository:


```shellscript
git clone <repository-url>
cd speaker-identification
```

2. Install dependencies:


```shellscript
npm install
# or
yarn install
```

3. Create a `.env.local` file with the following variables:


```plaintext
NEXT_PUBLIC_API_URL=/api
```

4. Start the development server:


```shellscript
npm run dev
# or
yarn dev
```

### Production Build

To create a production build:

```shellscript
npm run build
# or
yarn build
```

To start the production server:

```shellscript
npm run start
# or
yarn start
```

### Self-Hosting (Non-Vercel Deployment)

For deploying on your own server:

1. Build the application:


```shellscript
npm run build
# or
yarn build
```

2. Set up a Node.js server environment on your host
3. Configure a reverse proxy (like Nginx or Apache) to serve the Next.js application:


Example Nginx configuration:

```plaintext
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # For serving audio files directly
    location /audio-files/ {
        alias /path/to/your/audio/files/;
        autoindex off;
    }
}
```

4. Set up process management with PM2:


```shellscript
npm install -g pm2
pm2 start npm --name "speaker-id-frontend" -- start
pm2 save
pm2 startup
```

5. Configure environment variables on your server:


```shellscript
# Create a .env file in your project root
echo "NEXT_PUBLIC_API_URL=/api" > .env
```

## Complete Package List

Here's a full list of dependencies you'll need to install:

```json
"dependencies": {
  "@radix-ui/react-avatar": "^1.0.4",
  "@radix-ui/react-checkbox": "^1.0.4",
  "@radix-ui/react-dialog": "^1.0.5",
  "@radix-ui/react-dropdown-menu": "^2.0.6",
  "@radix-ui/react-label": "^2.0.2",
  "@radix-ui/react-progress": "^1.0.3",
  "@radix-ui/react-slider": "^1.1.2",
  "@radix-ui/react-slot": "^1.0.2",
  "@radix-ui/react-tabs": "^1.0.4",
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.1.0",
  "lucide-react": "^0.309.0",
  "next": "14.0.4",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "tailwind-merge": "^2.2.0",
  "tailwindcss-animate": "^1.0.7"
},
"devDependencies": {
  "@types/node": "^20.10.6",
  "@types/react": "^18.2.46",
  "@types/react-dom": "^18.2.18",
  "autoprefixer": "^10.4.16",
  "eslint": "^8.56.0",
  "eslint-config-next": "14.0.4",
  "postcss": "^8.4.32",
  "tailwindcss": "^3.4.0",
  "typescript": "^5.3.3"
}
```

## Backend Connections

The frontend expects the following API endpoints to be available from your Python backend:

### Audio Processing

| Endpoint | Method | Description | Location in Code
|-----|-----|-----|-----
| `/api/process` | POST | Upload and process an audio file | `lib/api-mock.ts` → `processAudioFile()`
| `/api/process/:id` | GET | Get processing status | `lib/api-mock.ts` → `getProcessingStatus()`


### Conversations

| Endpoint | Method | Description | Location in Code
|-----|-----|-----|-----
| `/api/conversations` | GET | Get all conversations | `lib/api-mock.ts` → `getConversations()`
| `/api/conversations/:id` | GET | Get a specific conversation | `lib/api-mock.ts` → `getConversation()`


### Speakers

| Endpoint | Method | Description | Location in Code
|-----|-----|-----|-----
| `/api/speakers` | GET | Get all speakers | `lib/api-mock.ts` → `getSpeakers()`
| `/api/speakers/rename` | POST | Rename a speaker | `lib/api-mock.ts` → `renameSpeaker()`


### Audio Files

| Endpoint | Method | Description | Location in Code
|-----|-----|-----|-----
| `/api/audio/:id` | GET | Get full conversation audio | `lib/api-mock.ts` → `getAudioUrl()`
| `/api/audio/:id/segments/:segmentId` | GET | Get segment audio (optional) | `lib/api-mock.ts` → `getAudioUrl()`


## Data Models

The frontend expects the following data structures from your backend:

### Speaker

```typescript
interface Speaker {
  id: string;
  name: string;
  isUnknown: boolean;
  confidence?: number;
  appearances?: number;
}
```

### Conversation

```typescript
interface Conversation {
  id: string;
  filename: string;
  duration: number;
  created: string;
  segments: TranscriptSegment[];
}

interface TranscriptSegment {
  id: string;
  start: number;
  end: number;
  text: string;
  speaker: SpeakerMatch;
}

interface SpeakerMatch {
  speakerId: string;
  speakerName: string;
  confidence: number;
  isUnknown: boolean;
}
```

### Processing Status

```typescript
interface ProcessingStatus {
  id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  stage?: string;
  progress?: number;
  error?: string;
}
```

## Connecting to Your Backend

To connect this frontend to your Python backend:

1. Replace the mock API functions in `lib/api-mock.ts` with real API calls to your backend
2. Update the `getAudioUrl` function to point to your actual audio file locations
3. Ensure your backend returns data in the expected format (see Data Models above)


Example of replacing a mock API function:

```typescript
// Before (mock)
export async function getSpeakers(): Promise<Speaker[]> {
  await new Promise(resolve => setTimeout(resolve, 700));
  return mockSpeakers;
}

// After (real API)
export async function getSpeakers(): Promise<Speaker[]> {
  const response = await fetch('/api/speakers');
  if (!response.ok) {
    throw new Error('Failed to fetch speakers');
  }
  return response.json();
}
```

## Audio File Handling

The frontend expects audio files to be accessible via URLs. There are two approaches you can take:

1. **Serve audio files directly**: Configure your web server to serve audio files from a directory
2. **Stream audio through API**: Create API endpoints that stream audio data from your storage


The `AudioPlayer` component is designed to work with both approaches and supports:

- Full conversation playback
- Segment-specific playback (playing only a portion of the audio)
- Volume control and playback position seeking


### Serving Audio Files Directly

If you choose to serve audio files directly from your server, you'll need to:

1. Configure your web server (Nginx, Apache, etc.) to serve files from your audio directory
2. Update the `getAudioUrl` function to point to the correct paths:


```typescript
export function getAudioUrl(conversationId: string, segmentId?: string): string {
  if (segmentId) {
    return `/audio-files/${conversationId}/segments/${segmentId}.wav`;
  }
  return `/audio-files/${conversationId}/full.wav`;
}
```

### Streaming Audio Through API

If you prefer to stream audio through your API:

1. Create API endpoints in your Python backend that stream audio data
2. Keep the existing URL structure in `getAudioUrl`


## Integration with Python Backend

### API Integration

The frontend is designed to work with a Python backend. To integrate:

1. Create API endpoints in your Python application that match the expected endpoints
2. Ensure your endpoints return data in the expected format
3. Update the API functions in `lib/api-mock.ts` to call your actual endpoints


### Python Flask Example

Here's a simple example of how you might implement some of these endpoints using Flask:

```python
from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    # Your code to fetch conversations from your database/files
    conversations = [...]  # Your data here
    return jsonify(conversations)

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    # Your code to fetch a specific conversation
    conversation = {...}  # Your data here
    return jsonify(conversation)

@app.route('/api/audio/<conversation_id>', methods=['GET'])
def get_audio(conversation_id):
    # Path to your audio file
    audio_path = f"./data/audio/{conversation_id}.wav"
    return send_file(audio_path, mimetype='audio/wav')

@app.route('/api/process', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    # Your code to save and process the file
    # ...
    
    return jsonify({
        "id": "process-id",
        "filename": file.filename,
        "status": "queued"
    })

if __name__ == '__main__':
    app.run(debug=True)
```

## Environment Variables

The following environment variables can be configured:

- `NEXT_PUBLIC_API_URL`: Base URL for API requests (default: `/api`)
- `CONVERSATIONS_DIR`: Directory for conversation data (for backend)
- `UPLOADS_DIR`: Directory for uploaded audio files (for backend)
- `PROCESSING_STATUS_DIR`: Directory for processing status files (for backend)


## Troubleshooting

### Common Issues

1. **Audio not playing**: Check that your audio files are accessible via the URLs specified in `getAudioUrl`
2. **API endpoints not found**: Ensure your backend is running and the endpoints match the expected paths
3. **CORS errors**: Configure your backend to allow cross-origin requests from your frontend


### CORS Configuration

If you're running the frontend and backend on different domains or ports, you'll need to configure CORS on your backend:

For Flask:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

For Express:

```javascript
const cors = require('cors');
app.use(cors());
```

## License

[MIT License](LICENSE)