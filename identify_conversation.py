import sys
import os
import assemblyai as aai
from pinecone import Pinecone
from nemo.collections.asr.models import EncDecSpeakerLabelModel
import torch
import numpy as np
from pydub import AudioSegment
from datetime import datetime

# Initialize APIs
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("speaker-embeddings")

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

def test_voice_segment(audio_segment, speaker_model, confidence_threshold=0.40):
    """Test a voice segment against the speaker database"""
    # Save segment to temporary file
    temp_wav = "temp_segment.wav"
    audio_segment.export(temp_wav, format="wav")
    
    try:
        # Generate embedding
        embedding = speaker_model.get_embedding(temp_wav)
        
        # Query database
        results = index.query(
            vector=embedding.tolist(),
            top_k=1,  # We only need the best match
            include_metadata=True
        )
        
        if results["matches"]:
            match = results["matches"][0]
            if match["score"] >= confidence_threshold:
                return match["metadata"]["speaker_name"], match["score"]
    
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
    
    return None, 0.0

def process_conversation(audio_file):
    """Process a conversation audio file and identify speakers"""
    # Convert to WAV if needed
    wav_file = convert_to_wav(audio_file)
    
    try:
        # Get transcript with speaker diarization
        transcript = transcribe(wav_file)
        
        # Load the full audio file
        full_audio = AudioSegment.from_file(wav_file)
        
        # Load speaker recognition model
        print("\nLoading speaker recognition model...")
        speaker_model = EncDecSpeakerLabelModel.from_pretrained("nvidia/speakerverification_en_titanet_large")
        
        # Process each utterance
        print("\nIdentifying speakers...")
        identified_utterances = []
        for utterance in transcript["utterances"]:
            # Extract audio segment
            start_ms = utterance["start"]
            end_ms = utterance["end"]
            segment = full_audio[start_ms:end_ms]
            
            # Test segment against database
            speaker_name, confidence = test_voice_segment(segment, speaker_model)
            
            # Use identified name or keep original speaker label
            if speaker_name:
                print(f"Identified {utterance['speaker']} as {speaker_name} ({confidence:.1%} confidence)")
                utterance["speaker"] = speaker_name
            
            identified_utterances.append(utterance)
        
        # Save transcript to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"transcript_{timestamp}.txt"
        
        with open(output_file, "w") as f:
            f.write("Conversation Transcript\n")
            f.write("=====================\n\n")
            for utterance in identified_utterances:
                f.write(f"{utterance['speaker']}: {utterance['text']}\n\n")
        
        print(f"\nTranscript saved to: {output_file}")
        
    finally:
        # Clean up temporary WAV file if we created one
        if wav_file.endswith('_temp.wav'):
            os.remove(wav_file)
            print(f"Cleaned up temporary file: {wav_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python identify_conversation.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"Error: File {audio_file} does not exist")
        sys.exit(1)
    
    process_conversation(audio_file)

if __name__ == "__main__":
    main() 