import sys
import os
from pinecone import Pinecone
from nemo.collections.asr.models import EncDecSpeakerLabelModel
import torch
import numpy as np
import uuid
from pydub import AudioSegment
import argparse

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

def check_speaker_exists(index, speaker_name):
    """Check if a speaker already exists in the database"""
    results = index.query(
        vector=[0.0] * 192,  # Dummy vector for metadata-only search
        top_k=1,
        include_metadata=True,
        filter={"speaker_name": {"$eq": speaker_name}}
    )
    return len(results['matches']) > 0

def delete_speaker(index, speaker_name):
    """Delete all embeddings for a speaker"""
    results = index.query(
        vector=[0.0] * 192,  # Dummy vector for metadata-only search
        top_k=1000,  # Increase if needed
        include_metadata=True,
        filter={"speaker_name": {"$eq": speaker_name}}
    )
    
    if not results['matches']:
        print(f"No embeddings found for speaker: {speaker_name}")
        return 0
    
    for match in results['matches']:
        index.delete(ids=[match['id']])
    
    count = len(results['matches'])
    print(f"Deleted {count} embeddings for speaker: {speaker_name}")
    return count

def delete_single_embedding(index, embedding_id):
    """Delete a single embedding by ID"""
    # First verify the embedding exists
    results = index.fetch(ids=[embedding_id])
    if not results['vectors']:
        print(f"No embedding found with ID: {embedding_id}")
        return False
    
    # Get the speaker name for the message
    speaker_name = results['vectors'][embedding_id]['metadata']['speaker_name']
    
    # Delete the embedding
    index.delete(ids=[embedding_id])
    print(f"Deleted embedding {embedding_id} belonging to speaker: {speaker_name}")
    return True

def add_speaker_embedding(index, wav_file, speaker_name, is_new_speaker=True):
    """Add a speaker's voice embedding to Pinecone from a WAV file"""
    # Check if speaker exists when adding new speaker
    if is_new_speaker and check_speaker_exists(index, speaker_name):
        print(f"Error: Speaker '{speaker_name}' already exists in the database.")
        print("Use --add-embedding to add an additional embedding for this speaker.")
        return False
    
    # Check if speaker exists when adding embedding
    if not is_new_speaker and not check_speaker_exists(index, speaker_name):
        print(f"Error: Speaker '{speaker_name}' does not exist in the database.")
        print("Use --add-speaker to add a new speaker.")
        return False
    
    # Load the speaker recognition model
    print("Loading speaker recognition model...")
    speaker_model = EncDecSpeakerLabelModel.from_pretrained("nvidia/speakerverification_en_titanet_large")
    
    # Convert file to WAV if needed
    wav_file = convert_to_wav(wav_file)
    
    try:
        # Generate embedding
        print(f"Generating voice embedding for {speaker_name}...")
        embedding = speaker_model.get_embedding(wav_file)
        
        # Convert embedding to the right format
        if isinstance(embedding, torch.Tensor):
            embedding_np = embedding.squeeze().cpu().numpy()
        elif isinstance(embedding, np.ndarray):
            embedding_np = embedding.squeeze()
        else:
            raise ValueError("Unsupported embedding type")

        if embedding_np.shape != (192,):
            raise ValueError(f"Expected embedding shape (192,), got {embedding_np.shape}")

        # Prepare for database
        embedding_list = embedding_np.tolist()
        unique_id = f"speaker_{speaker_name}_{uuid.uuid4().hex[:8]}"
        metadata = {"speaker_name": speaker_name}
        
        # Add to database
        print("Adding to speaker database...")
        index.upsert(vectors=[(unique_id, embedding_list, metadata)])
        print(f"Successfully added {speaker_name} to speaker database with ID {unique_id}")
        return True
        
    finally:
        # Clean up temporary WAV file if we created one
        if wav_file.endswith('_temp.wav'):
            os.remove(wav_file)
            print(f"Cleaned up temporary file: {wav_file}")

def list_speakers(index):
    """List all speakers and their embeddings in the database"""
    # Query with dummy vector to get all vectors
    results = index.query(
        vector=[0.0] * 192,
        top_k=1000,  # Increase if needed
        include_metadata=True
    )
    
    if not results['matches']:
        print("No speakers found in the database.")
        return
    
    # Group by speaker name
    speakers = {}
    for match in results['matches']:
        speaker_name = match['metadata']['speaker_name']
        if speaker_name not in speakers:
            speakers[speaker_name] = []
        speakers[speaker_name].append(match['id'])
    
    # Print results
    print("\nSpeakers in database:")
    print("--------------------")
    for speaker, embeddings in sorted(speakers.items()):
        print(f"\n{speaker}:")
        print(f"  Number of embeddings: {len(embeddings)}")
        print("  Embedding IDs:")
        for embedding_id in embeddings:
            print(f"    - {embedding_id}")

def main():
    parser = argparse.ArgumentParser(
        description='Manage voice embeddings in the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all speakers:
    %(prog)s --list

  Adding speakers:
    %(prog)s audio.wav "John Smith" --add-speaker      # New speaker
    %(prog)s audio.wav "John Smith" --add-embedding    # Additional embedding
  
  Deleting:
    %(prog)s speaker_John_Smith_abc123 --delete-embedding  # Delete specific embedding
    %(prog)s "John Smith" --delete-speaker                 # Delete speaker and all embeddings
""")
    
    # Add speaker arguments
    parser.add_argument('input', nargs='?', 
                      help='Audio file path for adding speakers, or speaker name/ID for deletion')
    parser.add_argument('speaker_name', nargs='?', help='Name of the speaker (for adding embeddings)')
    
    # Action flags
    parser.add_argument('--list', action='store_true',
                      help='List all speakers and their embeddings')
    parser.add_argument('--add-speaker', action='store_true',
                      help='Add a new speaker to the database')
    parser.add_argument('--add-embedding', action='store_true',
                      help='Add an additional embedding for an existing speaker')
    parser.add_argument('--delete-speaker', action='store_true',
                      help='Delete all embeddings for the specified speaker')
    parser.add_argument('--delete-embedding', action='store_true',
                      help='Delete a specific embedding by ID')
    
    args = parser.parse_args()
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("speaker-embeddings")
    
    # List speakers
    if args.list:
        list_speakers(index)
        return
    
    # Handle deletion operations
    if args.delete_speaker and args.input:
        delete_speaker(index, args.input)
        return
    
    if args.delete_embedding and args.input:
        delete_single_embedding(index, args.input)
        return
    
    # Handle adding embeddings
    if args.input and args.speaker_name:
        if not os.path.exists(args.input):
            print(f"Error: File {args.input} does not exist")
            sys.exit(1)
        
        if sum([args.add_speaker, args.add_embedding]) != 1:
            print("Error: Must specify exactly one of --add-speaker or --add-embedding")
            sys.exit(1)
        
        add_speaker_embedding(index, args.input, args.speaker_name, is_new_speaker=args.add_speaker)
    else:
        if not (args.list or args.delete_speaker or args.delete_embedding):
            parser.print_help()

if __name__ == "__main__":
    main() 