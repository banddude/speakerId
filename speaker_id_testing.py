import sys
import os
import json
import shutil
import assemblyai as aai
from pinecone import Pinecone
from nemo.collections.asr.models import EncDecSpeakerLabelModel
import torch
import numpy as np
from pydub import AudioSegment
from datetime import datetime
import uuid

# Initialize APIs
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("speaker-embeddings")

# Set custom HuggingFace cache directory in the project folder
os.environ["TRANSFORMERS_CACHE"] = os.path.join(os.getcwd(), "hf_cache")
os.environ["HF_HOME"] = os.path.join(os.getcwd(), "hf_cache")
os.makedirs(os.path.join(os.getcwd(), "hf_cache"), exist_ok=True)

# Base directory for processed conversations
PROCESSED_DIR = "processed_conversations"
UTTERANCES_DIR = "speaker_utterances"  # Keep backward compatibility for now

# Confidence threshold for automatic database updates
AUTO_UPDATE_CONFIDENCE_THRESHOLD = 0.70

def format_time(ms):
    """Format milliseconds as HH:MM:SS"""
    seconds = ms / 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def convert_to_wav(input_file):
    """Convert an audio file to WAV format if needed"""
    if input_file.lower().endswith('.wav'):
        return input_file
        
    print(f"Converting {input_file} to WAV format...")
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    wav_file = f"{base_filename}_temp.wav"
    
    # Load and convert the audio file
    audio = AudioSegment.from_file(input_file)
    
    # Convert to mono if stereo
    if audio.channels > 1:
        print("Converting to mono...")
        audio = audio.set_channels(1)
    
    # Export as WAV
    audio.export(wav_file, format="wav")
    print(f"File converted and saved as: {wav_file}")
    
    return wav_file

def transcribe(file_path):
    """Transcribe audio file using AssemblyAI"""
    print(f"\nTranscribing {file_path}...")
    config = aai.TranscriptionConfig(speaker_labels=True)
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(file_path)
    return transcript.json_response

def add_embedding_to_pinecone(embedding, speaker_name, source_file, is_short=False, duration_seconds=None):
    """Add an embedding to Pinecone with appropriate metadata"""
    # Generate unique ID
    unique_id = f"speaker_{speaker_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
    
    # Create metadata
    metadata = {
        "speaker_name": speaker_name,
        "source_file": os.path.basename(source_file),
        "is_short_utterance": is_short
    }
    
    # Add duration if provided
    if duration_seconds is not None:
        metadata["duration_seconds"] = duration_seconds
    
    # Convert embedding to correct format for Pinecone
    if isinstance(embedding, torch.Tensor):
        embedding_list = embedding.squeeze().cpu().numpy().tolist()
    elif isinstance(embedding, np.ndarray):
        embedding_list = embedding.squeeze().tolist()
    else:
        embedding_list = embedding.tolist()
    
    # Upload to Pinecone
    index.upsert(vectors=[(unique_id, embedding_list, metadata)])
    
    return unique_id

def check_if_embedding_exists(embedding, similarity_threshold=0.98):
    """Check if an embedding already exists in the database"""
    results = index.query(
        vector=embedding.tolist(),
        top_k=1,
        include_metadata=True
    )
    
    if results["matches"] and results["matches"][0]["score"] >= similarity_threshold:
        return True, results["matches"][0]["id"]
    
    return False, None

def test_voice_segment(audio_segment, speaker_model, confidence_threshold=0.40, is_short=False):
    """Test a voice segment against the speaker database"""
    # Save segment to temporary file
    temp_wav = "temp_segment.wav"
    audio_segment.export(temp_wav, format="wav")
    
    try:
        # Generate embedding
        embedding = speaker_model.get_embedding(temp_wav)
        
        # Special handling for very short utterances - log additional info
        segment_duration = len(audio_segment) / 1000.0  # Convert to seconds
        if segment_duration < 0.7:  # Less than 700ms
            is_short = True
            print(f"  Short utterance detected ({segment_duration:.2f} seconds)")
            
            # Look for top 2 matches to see candidates
            top_k = 2
        else:
            top_k = 1
            
        # Query database
        results = index.query(
            vector=embedding.tolist(),
            top_k=top_k,  # Get more matches for short utterances
            include_metadata=True
        )
        
        if results["matches"]:
            match = results["matches"][0]
            
            # For short utterances, print more details
            if is_short:
                print(f"  Top matches:")
                for i, match_result in enumerate(results["matches"]):
                    is_short_sample = match_result["metadata"].get("is_short_utterance", False)
                    print(f"   {i+1}. {match_result['metadata']['speaker_name']} "
                          f"(score: {match_result['score']:.4f}, "
                          f"short sample: {is_short_sample})")
            
            if match["score"] >= confidence_threshold:
                return match["metadata"]["speaker_name"], match["score"], match["id"], embedding
    
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
    
    return None, 0.0, None, embedding

def identify_unknown_speakers_by_combining(utterance_metadata, conversation_info, full_audio, speaker_model):
    """Combine utterances from unknown speakers to create more robust samples for identification"""
    # Group utterances by unknown speaker ID
    unknown_speakers = {}
    for utterance in utterance_metadata:
        if utterance["speaker"].startswith("Unknown_"):
            if utterance["speaker"] not in unknown_speakers:
                unknown_speakers[utterance["speaker"]] = []
            unknown_speakers[utterance["speaker"]].append(utterance)
    
    if not unknown_speakers:
        return utterance_metadata
        
    print(f"Found {len(unknown_speakers)} unknown speaker(s) to process")
    
    # Process each unknown speaker group
    for unknown_speaker, utterances in unknown_speakers.items():
        print(f"\nProcessing combined utterances for {unknown_speaker} ({len(utterances)} utterances)...")
        
        # Combine all utterances into one audio segment
        combined_audio = AudioSegment.empty()
        for utterance in utterances:
            segment = full_audio[utterance["start_ms"]:utterance["end_ms"]]
            combined_audio += segment
            
        # Skip if combined audio is still too short
        if len(combined_audio) < 1000:  # 1 second
            print(f"  Combined audio still too short ({len(combined_audio)}ms), skipping")
            continue
        
        print(f"  Combined audio length: {len(combined_audio)}ms")
        
        # Identify the combined audio
        temp_file = "temp_combined.wav"
        combined_audio.export(temp_file, format="wav")
        
        try:
            # Test the combined sample against database
            embedding = speaker_model.get_embedding(temp_file)
            results = index.query(
                vector=embedding.tolist(),
                top_k=1,
                include_metadata=True
            )
            
            if results["matches"] and results["matches"][0]["score"] >= 0.40:
                match = results["matches"][0]
                speaker_name = match["metadata"]["speaker_name"]
                confidence = match["score"]
                embedding_id = match["id"]
                
                print(f"  ✅ Identified as {speaker_name} (confidence: {confidence:.4f})")
                
                # Normalize speaker name for directory
                speaker_dir_name = speaker_name.replace(" ", "_")
                
                # Create the new speaker directory if needed
                new_speaker_dir = os.path.join(conversation_info["speakers_dir"], speaker_dir_name)
                if not os.path.exists(new_speaker_dir):
                    os.makedirs(new_speaker_dir, exist_ok=True)
                
                # Reassign all utterances from this unknown speaker
                for utterance in utterances:
                    old_speaker = utterance["speaker"]
                    old_speaker_dir_name = old_speaker.replace(" ", "_")
                    
                    # Update the metadata
                    utterance["speaker"] = speaker_name
                    utterance["confidence"] = confidence
                    utterance["embedding_id"] = embedding_id
                    utterance["combined_identification"] = True
                    
                    # Move the symlink to the correct speaker directory
                    old_speaker_dir = os.path.join(conversation_info["speakers_dir"], old_speaker_dir_name)
                    
                    # Move the symlink
                    utterance_file = f"{utterance['id']}.wav"
                    old_path = os.path.join(old_speaker_dir, utterance_file)
                    new_path = os.path.join(new_speaker_dir, utterance_file)
                    
                    # Get the target of the symlink
                    if os.path.exists(old_path):
                        try:
                            # For symlinks
                            if os.path.islink(old_path):
                                target = os.readlink(old_path)
                                if os.path.exists(new_path):
                                    os.remove(new_path)
                                os.symlink(target, new_path)
                                os.remove(old_path)
                            else:
                                # For regular files (if not using symlinks)
                                shutil.copy2(old_path, new_path)
                                os.remove(old_path)
                        except (OSError, FileNotFoundError) as e:
                            print(f"  Error moving file: {e}")
                
                # Remove empty directory if needed
                if os.path.exists(old_speaker_dir) and not os.listdir(old_speaker_dir):
                    try:
                        os.rmdir(old_speaker_dir)
                        print(f"  Removed empty directory: {old_speaker_dir}")
                    except OSError as e:
                        print(f"  Error removing directory: {e}")
            else:
                if results["matches"]:
                    print(f"  ❌ Match found but confidence too low: {results['matches'][0]['metadata']['speaker_name']} (confidence: {results['matches'][0]['score']:.4f})")
                else:
                    print(f"  ❌ No matches found for combined utterances")
                
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    return utterance_metadata

def save_utterance_legacy(audio_segment, speaker_name, conversation_name, utterance_text, utterance_id):
    """Save an utterance to the appropriate speaker folder (legacy method)"""
    # Create speaker directory if it doesn't exist
    speaker_dir = os.path.join(UTTERANCES_DIR, speaker_name)
    os.makedirs(speaker_dir, exist_ok=True)
    
    # Create filename with conversation name and utterance ID
    safe_conv_name = os.path.splitext(os.path.basename(conversation_name))[0]
    filename = f"{safe_conv_name}_utterance_{utterance_id}.wav"
    filepath = os.path.join(speaker_dir, filename)
    
    # Save audio
    audio_segment.export(filepath, format="wav")
    
    # Save text in accompanying file
    text_filepath = f"{os.path.splitext(filepath)[0]}.txt"
    with open(text_filepath, "w") as f:
        f.write(utterance_text)
    
    return filepath

def create_conversation_dir(audio_file):
    """Create a conversation directory with the new structure"""
    # Generate a timestamp-based ID for the conversation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conversation_id = f"conversation_{timestamp}"
    
    # Create the main conversation directory
    conversation_dir = os.path.join(PROCESSED_DIR, conversation_id)
    os.makedirs(conversation_dir, exist_ok=True)
    
    # Create subdirectories
    utterances_dir = os.path.join(conversation_dir, "utterances")
    speakers_dir = os.path.join(conversation_dir, "speakers")
    os.makedirs(utterances_dir, exist_ok=True)
    os.makedirs(speakers_dir, exist_ok=True)
    
    # Copy original audio file
    original_ext = os.path.splitext(audio_file)[1]
    original_audio_path = os.path.join(conversation_dir, f"original_audio{original_ext}")
    shutil.copy2(audio_file, original_audio_path)
    
    return {
        "id": conversation_id,
        "dir": conversation_dir,
        "utterances_dir": utterances_dir,
        "speakers_dir": speakers_dir,
        "original_audio": original_audio_path
    }

def save_utterance(audio_segment, utterance_data, conversation_info, utterance_id):
    """Save an utterance using the new structure"""
    # Generate utterance filename
    utterance_filename = f"utterance_{utterance_id:03d}.wav"
    utterance_path = os.path.join(conversation_info["utterances_dir"], utterance_filename)
    
    # Save the audio segment
    audio_segment.export(utterance_path, format="wav")
    
    # Get speaker name and create normalized version for folder name
    speaker_name = utterance_data["speaker"]
    speaker_dir_name = speaker_name.replace(" ", "_")
    
    # Create speaker directory if it doesn't exist
    speaker_dir = os.path.join(conversation_info["speakers_dir"], speaker_dir_name)
    os.makedirs(speaker_dir, exist_ok=True)
    
    # Create symlink or copy in speaker directory
    speaker_utterance_path = os.path.join(speaker_dir, utterance_filename)
    
    try:
        # Try creating a symlink (works on Linux/Mac)
        rel_path = os.path.relpath(utterance_path, os.path.dirname(speaker_utterance_path))
        if os.path.exists(speaker_utterance_path):
            os.remove(speaker_utterance_path)  # Remove existing symlink/file if present
        os.symlink(rel_path, speaker_utterance_path)
    except (OSError, AttributeError):
        # Fallback to copy on Windows or if symlinks not supported
        shutil.copy2(utterance_path, speaker_utterance_path)
    
    # Create utterance metadata
    return {
        "id": f"utterance_{utterance_id:03d}",
        "start_time": format_time(utterance_data["start"]),
        "end_time": format_time(utterance_data["end"]),
        "start_ms": utterance_data["start"],
        "end_ms": utterance_data["end"],
        "speaker": speaker_name,
        "text": utterance_data["text"],
        "confidence": utterance_data.get("confidence", 0.0),
        "embedding_id": utterance_data.get("embedding_id", None),
        "audio_file": os.path.join("utterances", utterance_filename)
    }

def process_conversation(audio_file):
    """Process a conversation audio file and identify speakers"""
    # Make base directories
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(UTTERANCES_DIR, exist_ok=True)  # Keep for backward compatibility
    
    # Convert to WAV if needed
    wav_file = convert_to_wav(audio_file)
    conversation_name = os.path.basename(audio_file)
    
    # Track statistics for short utterances
    short_utterance_stats = {
        "total": 0,
        "identified_directly": 0,
        "identified_combined": 0,
        "unidentified": 0
    }
    
    # Track statistics for database updates
    db_update_stats = {
        "added": 0,
        "skipped_low_confidence": 0,
        "skipped_unknown": 0,
        "skipped_duplicate": 0
    }
    
    try:
        # Create conversation directory structure
        conversation_info = create_conversation_dir(audio_file)
        
        # Get transcript with speaker diarization
        transcript = transcribe(wav_file)
        
        # Get audio duration
        audio_duration = transcript.get("audio_duration", 0)
        
        # Load the full audio file
        full_audio = AudioSegment.from_file(wav_file)
        
        # Load speaker recognition model
        print("\nLoading speaker recognition model...")
        model_path = "models/titanet_large.nemo"
        
        speaker_model = None
        # Try loading from local file first
        if os.path.exists(model_path):
            try:
                speaker_model = EncDecSpeakerLabelModel.restore_from(model_path)
                print(f"Loaded model from local path: {model_path}")
            except Exception as e:
                print(f"Error loading local model: {e}")
                
        # If local loading failed, try downloading
        if speaker_model is None:
            try:
                print("Trying to download model from NGC...")
                speaker_model = EncDecSpeakerLabelModel.from_pretrained(model_name="titanet_large")
                
                # Save for future use
                os.makedirs("models", exist_ok=True)
                speaker_model.save_to(model_path)
                print(f"Model saved to: {model_path} for future use")
            except Exception as e:
                print(f"Error downloading model: {e}")
                print("\nPlease run direct_model_download.py first to download the model.")
                raise Exception("Could not load speaker recognition model. Run direct_model_download.py first.")
        
        # Process each utterance
        print("\nIdentifying speakers and saving utterances...")
        identified_utterances = []
        utterance_paths = {}  # To track saved utterances by speaker
        utterance_metadata = []  # For the metadata.json file
        
        for i, utterance in enumerate(transcript["utterances"]):
            # Extract audio segment
            start_ms = utterance["start"]
            end_ms = utterance["end"]
            segment = full_audio[start_ms:end_ms]
            
            # Calculate duration in seconds
            duration_seconds = (end_ms - start_ms) / 1000.0
            
            # Check if this is a short utterance
            is_short = duration_seconds < 0.7  # Less than 700ms
            if is_short:
                short_utterance_stats["total"] += 1
                
            # Test segment against database
            speaker_name, confidence, embedding_id, embedding = test_voice_segment(segment, speaker_model)
            
            # Track identification of short utterances
            if is_short and speaker_name:
                short_utterance_stats["identified_directly"] += 1
                print(f"  ✅ Short utterance directly identified as {speaker_name}")
            
            # Use identified name or create unknown speaker name
            if not speaker_name:
                # Create a unique ID for the unknown speaker within this conversation
                original_speaker = utterance.get('speaker', f'speaker_{i}')  # This is usually 'speaker_0', 'speaker_1', etc.
                speaker_name = f"Unknown_{original_speaker}"
                db_update_stats["skipped_unknown"] += 1
            else:
                # Check if this utterance should be added to the database
                if confidence >= AUTO_UPDATE_CONFIDENCE_THRESHOLD:
                    # Check if very similar embedding already exists
                    is_duplicate, duplicate_id = check_if_embedding_exists(embedding)
                    
                    if is_duplicate:
                        print(f"  Skipping database update - very similar embedding already exists (ID: {duplicate_id})")
                        db_update_stats["skipped_duplicate"] += 1
                    else:
                        # Add to database
                        utterance_path = os.path.join(conversation_info["utterances_dir"], f"utterance_{i:03d}.wav")
                        new_id = add_embedding_to_pinecone(
                            embedding, 
                            speaker_name, 
                            utterance_path, 
                            is_short=is_short,
                            duration_seconds=duration_seconds
                        )
                        print(f"  🔄 Added high-quality utterance to database (ID: {new_id}, confidence: {confidence:.4f})")
                        db_update_stats["added"] += 1
                else:
                    print(f"  Skipping database update - confidence too low ({confidence:.4f} < {AUTO_UPDATE_CONFIDENCE_THRESHOLD})")
                    db_update_stats["skipped_low_confidence"] += 1
            
            # Add speaker and confidence information to utterance
            utterance["speaker"] = speaker_name
            utterance["confidence"] = confidence
            utterance["embedding_id"] = embedding_id
            utterance["is_short"] = is_short
            
            # Save utterance using new structure
            utterance_meta = save_utterance(segment, utterance, conversation_info, i)
            utterance_metadata.append(utterance_meta)
            
            # Also save using legacy method for backward compatibility
            legacy_path = save_utterance_legacy(
                segment, 
                speaker_name, 
                conversation_name, 
                utterance["text"],
                i
            )
            
            # Track utterance
            if speaker_name not in utterance_paths:
                utterance_paths[speaker_name] = []
            utterance_paths[speaker_name].append(legacy_path)
            
            # Update utterance for transcript
            identified_utterances.append(utterance)
            
            # Print progress
            if is_short:
                print(f"Utterance {i+1}/{len(transcript['utterances'])}: {speaker_name} - {utterance['text'][:50]}... (short)")
            else:
                print(f"Utterance {i+1}/{len(transcript['utterances'])}: {speaker_name} - {utterance['text'][:50]}...")
        
        # Try to identify unknown speakers by combining their utterances
        if any(u["speaker"].startswith("Unknown_") for u in utterance_metadata):
            print("\nAttempting to identify unknown speakers by combining their utterances...")
            utterance_metadata = identify_unknown_speakers_by_combining(
                utterance_metadata, conversation_info, full_audio, speaker_model
            )
            
            # Update the identified_utterances list to match the updated speaker assignments
            for i, utterance in enumerate(identified_utterances):
                if i < len(utterance_metadata):  # Safety check
                    # Check if this speaker was identified through combining and is a short utterance
                    if utterance.get("is_short", False) and "combined_identification" in utterance_metadata[i]:
                        short_utterance_stats["identified_combined"] += 1
                    
                    utterance["speaker"] = utterance_metadata[i]["speaker"]
                    if "combined_identification" in utterance_metadata[i]:
                        utterance["combined_identification"] = utterance_metadata[i]["combined_identification"]
            
            # Count unidentified short utterances
            for utterance in utterance_metadata:
                if utterance.get("is_short", False) and utterance["speaker"].startswith("Unknown_"):
                    short_utterance_stats["unidentified"] += 1
        
        # Create metadata.json
        speakers_list = list(set([u["speaker"] for u in utterance_metadata]))
        metadata = {
            "conversation_id": conversation_info["id"],
            "original_audio": os.path.basename(conversation_info["original_audio"]),
            "date_processed": datetime.now().isoformat(),
            "duration_seconds": audio_duration,
            "speakers": speakers_list,
            "utterances": utterance_metadata,
            "short_utterance_stats": short_utterance_stats,
            "database_update_stats": db_update_stats
        }
        
        # Save metadata.json
        metadata_path = os.path.join(conversation_info["dir"], "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Save transcript to the conversation directory
        transcript_path = os.path.join(conversation_info["dir"], "transcript.txt")
        with open(transcript_path, "w") as f:
            f.write(f"Conversation Transcript: {conversation_name}\n")
            f.write("=====================\n\n")
            for utterance in identified_utterances:
                start_time = format_time(utterance["start"])
                end_time = format_time(utterance["end"])
                f.write(f"[{utterance['speaker']} {start_time}-{end_time}]: {utterance['text']}\n\n")
        
        # Also save a legacy transcript (backward compatibility)
        legacy_transcript = f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(legacy_transcript, "w") as f:
            f.write(f"Conversation Transcript: {conversation_name}\n")
            f.write("=====================\n\n")
            for utterance in identified_utterances:
                f.write(f"{utterance['speaker']}: {utterance['text']}\n\n")
        
        print(f"\nConversation processed and saved to: {conversation_info['dir']}")
        print(f"Transcript saved to: {transcript_path}")
        print(f"Legacy transcript saved to: {legacy_transcript}")
        
        # Print summary of saved utterances
        print("\nSaved utterances by speaker:")
        for speaker in speakers_list:
            speaker_utterances = [u for u in utterance_metadata if u["speaker"] == speaker]
            print(f"  {speaker}: {len(speaker_utterances)} utterances")
        
        # Print short utterance stats
        print("\nShort utterance statistics:")
        print(f"  Total short utterances: {short_utterance_stats['total']}")
        print(f"  Directly identified: {short_utterance_stats['identified_directly']}")
        print(f"  Identified by combining: {short_utterance_stats['identified_combined']}")
        print(f"  Unidentified: {short_utterance_stats['unidentified']}")
        
        # Print database update stats
        print("\nDatabase update statistics:")
        print(f"  Added to database: {db_update_stats['added']} new utterances")
        print(f"  Skipped (low confidence): {db_update_stats['skipped_low_confidence']} utterances")
        print(f"  Skipped (unknown speakers): {db_update_stats['skipped_unknown']} utterances")
        print(f"  Skipped (duplicates): {db_update_stats['skipped_duplicate']} utterances")
            
        return conversation_info["dir"], metadata
            
    finally:
        # Clean up temporary WAV file if we created one
        if wav_file.endswith('_temp.wav'):
            os.remove(wav_file)
            print(f"Cleaned up temporary file: {wav_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python speaker_id_testing.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"Error: File {audio_file} does not exist")
        sys.exit(1)
    
    process_conversation(audio_file)

if __name__ == "__main__":
    main() 