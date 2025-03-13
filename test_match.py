import sys
import os
from pinecone import Pinecone
from nemo.collections.asr.models import EncDecSpeakerLabelModel
import torch
import numpy as np
from pydub import AudioSegment
import argparse
from collections import defaultdict

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

def test_match(audio_file, top_k=5):
    """Test an audio file against all speaker embeddings in the database"""
    print(f"\nTesting audio file: {audio_file}")
    
    # Load the speaker recognition model
    print("Loading speaker recognition model...")
    speaker_model = EncDecSpeakerLabelModel.from_pretrained("nvidia/speakerverification_en_titanet_large")
    
    # Generate embedding for the test file
    print("Generating voice embedding...")
    embedding = speaker_model.get_embedding(audio_file)
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("speaker-embeddings")
    
    # Query the database
    print("\nQuerying speaker database...")
    results = index.query(
        vector=embedding.tolist(),
        top_k=top_k,
        include_metadata=True
    )
    
    # Group results by speaker
    speaker_matches = defaultdict(list)
    for match in results["matches"]:
        speaker_name = match["metadata"]["speaker_name"]
        speaker_matches[speaker_name].append({
            'id': match['id'],
            'score': match['score']
        })
    
    # Print results by speaker
    print("\nMatches by Speaker:")
    print("=" * 50)
    
    # Sort speakers by their best match score
    sorted_speakers = sorted(
        speaker_matches.items(),
        key=lambda x: max(m['score'] for m in x[1]),
        reverse=True
    )
    
    for speaker_name, matches in sorted_speakers:
        # Calculate statistics
        scores = [m['score'] for m in matches]
        avg_score = np.mean(scores)
        max_score = max(scores)
        
        print(f"\nSpeaker: {speaker_name}")
        print(f"Number of matching embeddings: {len(matches)}")
        print(f"Average confidence: {avg_score:.1%}")
        print(f"Best match confidence: {max_score:.1%}")
        print("\nIndividual embedding matches:")
        
        # Sort matches by score
        sorted_matches = sorted(matches, key=lambda x: x['score'], reverse=True)
        for match in sorted_matches:
            print(f"  - Embedding {match['id']}: {match['score']:.1%}")

def main():
    parser = argparse.ArgumentParser(description="Test an audio file against speaker database")
    parser.add_argument("audio_file", help="Path to the audio file to test")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top matches to return")
    args = parser.parse_args()
    
    if not os.path.exists(args.audio_file):
        print(f"Error: File {args.audio_file} does not exist")
        sys.exit(1)
    
    test_match(args.audio_file, args.top_k)

if __name__ == "__main__":
    main() 