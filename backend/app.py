from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import json
import uuid
from datetime import datetime
import logging

# Setup path for importing from parent directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import existing scripts
from utils.process_manager import start_processing, get_processing_status
from speaker_id_testing import process_conversation
from update_speaker_db_verified import update_speaker_database
from rename_speaker import rename_speaker_in_conversation

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS to allow requests from the frontend
# This is more explicit than the simple CORS(app) to ensure proper cross-origin support
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuration
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
CONVERSATIONS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'processed_conversations'))

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "speaker-id-api"
    })

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all processed conversations"""
    # Log the request for debugging
    logger.info(f"Received request for conversations from {request.remote_addr}")
    
    conversations = []
    
    # Walk through the processed_conversations directory
    try:
        conversation_dirs = os.listdir(CONVERSATIONS_FOLDER)
        logger.info(f"Found {len(conversation_dirs)} potential conversation directories")
        
        for conversation_dir in conversation_dirs:
            conversation_path = os.path.join(CONVERSATIONS_FOLDER, conversation_dir)
            
            # Only include directories
            if os.path.isdir(conversation_path):
                # Check for metadata.json
                metadata_path = os.path.join(conversation_path, 'metadata.json')
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        # Create summary for the frontend
                        conversation_summary = {
                            'id': conversation_dir,
                            'filename': metadata.get('original_audio', 'Unknown'),
                            'duration': metadata.get('duration_seconds', 0),
                            'created': metadata.get('date_processed', datetime.now().isoformat()),
                            'segments': []
                        }
                        
                        # Add utterances as segments
                        for utterance in metadata.get('utterances', []):
                            segment = {
                                'id': utterance.get('id', ''),
                                'start': utterance.get('start_ms', 0) / 1000,  # Convert to seconds
                                'end': utterance.get('end_ms', 0) / 1000,      # Convert to seconds
                                'text': utterance.get('text', ''),
                                'speaker': {
                                    'speakerId': utterance.get('embedding_id', ''),
                                    'speakerName': utterance.get('speaker', 'Unknown'),
                                    'confidence': utterance.get('confidence', 0) * 100,  # Convert to percentage
                                    'isUnknown': utterance.get('speaker', '').lower() == 'unknown'
                                }
                            }
                            conversation_summary['segments'].append(segment)
                        
                        conversations.append(conversation_summary)
                    except Exception as e:
                        logger.error(f"Error processing conversation {conversation_dir}: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing conversation directories: {str(e)}")
        return jsonify({"error": f"Error listing conversations: {str(e)}"}), 500
    
    # Sort by creation date (newest first)
    conversations.sort(key=lambda x: x['created'], reverse=True)
    logger.info(f"Returning {len(conversations)} conversations")
    return jsonify(conversations)

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation by ID"""
    conversation_path = os.path.join(CONVERSATIONS_FOLDER, conversation_id)
    
    if not os.path.exists(conversation_path):
        return jsonify({"error": "Conversation not found"}), 404
    
    metadata_path = os.path.join(conversation_path, 'metadata.json')
    if not os.path.exists(metadata_path):
        return jsonify({"error": "Conversation metadata not found"}), 404
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Format conversation for the frontend
        conversation = {
            'id': conversation_id,
            'filename': metadata.get('original_audio', 'Unknown'),
            'duration': metadata.get('duration_seconds', 0),
            'created': metadata.get('date_processed', datetime.now().isoformat()),
            'segments': []
        }
        
        # Add utterances as segments
        for utterance in metadata.get('utterances', []):
            segment = {
                'id': utterance.get('id', ''),
                'start': utterance.get('start_ms', 0) / 1000,
                'end': utterance.get('end_ms', 0) / 1000,
                'text': utterance.get('text', ''),
                'speaker': {
                    'speakerId': utterance.get('embedding_id', ''),
                    'speakerName': utterance.get('speaker', 'Unknown'),
                    'confidence': utterance.get('confidence', 0) * 100,
                    'isUnknown': utterance.get('speaker', '').lower() == 'unknown'
                }
            }
            conversation['segments'].append(segment)
        
        return jsonify(conversation)
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
        return jsonify({"error": f"Error retrieving conversation: {str(e)}"}), 500

@app.route('/api/speakers', methods=['GET'])
def get_speakers():
    """Get all speakers from processed conversations"""
    speakers = {}
    
    # Walk through all conversations to collect speakers
    for conversation_dir in os.listdir(CONVERSATIONS_FOLDER):
        conversation_path = os.path.join(CONVERSATIONS_FOLDER, conversation_dir)
        
        # Only include directories
        if os.path.isdir(conversation_path):
            # Check for metadata.json
            metadata_path = os.path.join(conversation_path, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Process utterances to collect speakers
                    for utterance in metadata.get('utterances', []):
                        speaker_name = utterance.get('speaker', 'Unknown')
                        speaker_id = utterance.get('embedding_id', '')
                        confidence = utterance.get('confidence', 0)
                        
                        if speaker_id and speaker_name:
                            # Generate a consistent ID for the speaker
                            speaker_key = speaker_name.lower().replace(' ', '_')
                            
                            if speaker_key not in speakers:
                                speakers[speaker_key] = {
                                    'id': speaker_key,
                                    'name': speaker_name,
                                    'isUnknown': speaker_name.lower() == 'unknown',
                                    'confidence': confidence * 100,  # Convert to percentage
                                    'appearances': 1
                                }
                            else:
                                # Update existing speaker
                                speakers[speaker_key]['appearances'] += 1
                                # Update confidence with the max value
                                speakers[speaker_key]['confidence'] = max(
                                    speakers[speaker_key]['confidence'],
                                    confidence * 100
                                )
                except Exception as e:
                    logger.error(f"Error processing speakers in conversation {conversation_dir}: {str(e)}")
    
    # Convert to list and sort by name
    speakers_list = list(speakers.values())
    speakers_list.sort(key=lambda x: x['name'])
    
    return jsonify(speakers_list)

@app.route('/api/speakers/rename', methods=['POST'])
def rename_speaker():
    """Rename a speaker across all conversations"""
    data = request.json
    
    if not data or 'originalName' not in data or 'newName' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    original_name = data['originalName']
    new_name = data['newName']
    update_all = data.get('updateAllInstances', True)
    min_confidence = data.get('minConfidence', 70) / 100  # Convert from percentage
    
    try:
        updated_count = 0
        
        # Walk through all conversations
        for conversation_dir in os.listdir(CONVERSATIONS_FOLDER):
            conversation_path = os.path.join(CONVERSATIONS_FOLDER, conversation_dir)
            
            # Only process directories
            if os.path.isdir(conversation_path):
                # Check if speaker exists in this conversation
                speaker_dir = os.path.join(conversation_path, 'speakers', original_name)
                if os.path.exists(speaker_dir):
                    # Call the rename_speaker function from the existing script
                    result = rename_speaker_in_conversation(
                        conversation_path=conversation_path,
                        old_speaker=original_name,
                        new_speaker=new_name,
                        confidence_threshold=min_confidence
                    )
                    
                    if result:
                        updated_count += 1
        
        # Update the speaker database if requested
        if update_all and updated_count > 0:
            # This would need to be implemented based on your existing scripts
            pass
        
        return jsonify({
            "success": True,
            "updated": updated_count
        })
    except Exception as e:
        logger.error(f"Error renaming speaker {original_name} to {new_name}: {str(e)}")
        return jsonify({"error": f"Error renaming speaker: {str(e)}"}), 500

@app.route('/api/process', methods=['POST'])
def process_audio():
    """Upload and process a new audio file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Generate a unique ID for the processing job
        process_id = f"process_{str(uuid.uuid4())[:8]}"
        
        # Save the uploaded file
        filename = f"{process_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Start processing in a background thread
        status = start_processing(file_path, process_id)
        
        return jsonify({
            "id": process_id,
            "filename": file.filename,
            "status": status['status'],
            "progress": status['progress']
        })
    except Exception as e:
        logger.error(f"Error processing audio file: {str(e)}")
        return jsonify({"error": f"Error processing audio file: {str(e)}"}), 500

@app.route('/api/process/<process_id>', methods=['GET'])
def get_processing_status_endpoint(process_id):
    """Get the status of a processing job"""
    status = get_processing_status(process_id)
    
    if not status:
        return jsonify({"error": "Processing job not found"}), 404
    
    return jsonify({
        "id": process_id,
        "status": status['status'],
        "progress": status['progress'],
        "stage": status['stage'],
        "error": status['error'],
        "conversation_id": status.get('conversation_id')
    })

@app.route('/api/audio/<conversation_id>', methods=['GET'])
def get_audio(conversation_id):
    """Get the full audio file for a conversation"""
    conversation_path = os.path.join(CONVERSATIONS_FOLDER, conversation_id)
    
    if not os.path.exists(conversation_path):
        return jsonify({"error": "Conversation not found"}), 404
    
    # Look for the original audio file
    for file in os.listdir(conversation_path):
        if file.endswith(('.wav', '.mp3', '.m4a')):
            audio_path = os.path.join(conversation_path, file)
            return send_file(audio_path)
    
    return jsonify({"error": "Audio file not found"}), 404

@app.route('/api/audio/<conversation_id>/segments/<segment_id>', methods=['GET'])
def get_segment_audio(conversation_id, segment_id):
    """Get the audio for a specific segment/utterance"""
    conversation_path = os.path.join(CONVERSATIONS_FOLDER, conversation_id)
    
    if not os.path.exists(conversation_path):
        return jsonify({"error": "Conversation not found"}), 404
    
    # Look for the utterance audio file
    utterance_path = os.path.join(conversation_path, 'utterances', f"{segment_id}.wav")
    if os.path.exists(utterance_path):
        return send_file(utterance_path)
    
    return jsonify({"error": "Segment audio not found"}), 404

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info(f"Starting Flask application on port 5000")
    logger.info(f"CORS configured for origins: http://localhost:3000, http://127.0.0.1:3000")
    logger.info(f"Conversations folder: {CONVERSATIONS_FOLDER}")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    app.run(debug=True, port=5000) 