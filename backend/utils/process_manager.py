import os
import sys
import threading
import time
import json
from datetime import datetime
import logging
import shutil

# Setup path for importing from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the conversation processing function
from speaker_id_testing import process_conversation

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Store processing jobs
processing_jobs = {}

def process_audio_file(file_path, process_id):
    """
    Process an audio file in the background
    
    Args:
        file_path: Path to the audio file
        process_id: Unique ID for this processing job
    """
    try:
        # Update status to processing
        processing_jobs[process_id] = {
            'status': 'processing',
            'progress': 10,
            'stage': 'Starting transcription...',
            'start_time': datetime.now().isoformat(),
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'error': None
        }
        
        # Process the conversation
        logger.info(f"Processing audio file: {file_path}")
        
        # Update progress
        processing_jobs[process_id]['progress'] = 30
        processing_jobs[process_id]['stage'] = 'Transcribing audio...'
        
        # Call the actual processing function
        result = process_conversation(file_path)
        
        # Update progress
        processing_jobs[process_id]['progress'] = 80
        processing_jobs[process_id]['stage'] = 'Finalizing results...'
        
        # Update status to completed
        processing_jobs[process_id]['status'] = 'completed'
        processing_jobs[process_id]['progress'] = 100
        processing_jobs[process_id]['stage'] = 'Processing complete'
        processing_jobs[process_id]['completion_time'] = datetime.now().isoformat()
        processing_jobs[process_id]['conversation_id'] = result.get('conversation_id')
        
        logger.info(f"Processing completed for: {file_path}")
        
        # Clean up temporary files
        try:
            if os.path.exists(file_path) and file_path.startswith(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {file_path}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error processing audio file {file_path}: {str(e)}")
        # Update status to failed
        processing_jobs[process_id]['status'] = 'failed'
        processing_jobs[process_id]['error'] = str(e)

def start_processing(file_path, process_id):
    """
    Start processing an audio file in a background thread
    
    Args:
        file_path: Path to the audio file
        process_id: Unique ID for this processing job
        
    Returns:
        dict: Initial status of the processing job
    """
    # Initialize job status
    processing_jobs[process_id] = {
        'status': 'queued',
        'progress': 0,
        'stage': 'Queued for processing',
        'start_time': datetime.now().isoformat(),
        'file_path': file_path,
        'filename': os.path.basename(file_path),
        'error': None
    }
    
    # Start processing in a background thread
    thread = threading.Thread(
        target=process_audio_file,
        args=(file_path, process_id)
    )
    thread.daemon = True
    thread.start()
    
    return processing_jobs[process_id]

def get_processing_status(process_id):
    """
    Get the status of a processing job
    
    Args:
        process_id: ID of the processing job
        
    Returns:
        dict: Status of the processing job or None if not found
    """
    return processing_jobs.get(process_id)

def get_all_processing_jobs():
    """
    Get all processing jobs
    
    Returns:
        dict: All processing jobs
    """
    return processing_jobs 