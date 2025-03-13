#!/usr/bin/env python3
# Fix Hugging Face cache warning - set environment variables BEFORE imports
import os
import sys

# Create and set custom cache directories in the project folder
cache_dir = os.path.join(os.getcwd(), "hf_cache")
os.makedirs(cache_dir, exist_ok=True)

# Set ALL the relevant environment variables
os.environ["TRANSFORMERS_CACHE"] = cache_dir
os.environ["HF_HOME"] = cache_dir
os.environ["HF_DATASETS_CACHE"] = cache_dir
os.environ["HUGGINGFACE_HUB_CACHE"] = cache_dir
os.environ["HUGGINGFACE_ASSETS_CACHE"] = cache_dir
os.environ["XDG_CACHE_HOME"] = cache_dir

# Now import the rest
import argparse
from pinecone import Pinecone
from nemo.collections.asr.models import EncDecSpeakerLabelModel
import torch
import numpy as np
import uuid
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("speaker-embeddings")

def get_existing_embeddings(speaker_name):
    """Get existing embeddings for a speaker from Pinecone"""
    results = index.query(
        vector=[0.0] * 192,  # Dummy vector for metadata-only search
        top_k=100,  # Increase if needed for speakers with many embeddings
        include_metadata=True,
        include_values=True,
        filter={"speaker_name": {"$eq": speaker_name}}
    )
    
    embeddings = {}
    for match in results['matches']:
        embeddings[match['id']] = np.array(match['values'])
    
    return embeddings

def is_duplicate(new_embedding, existing_embeddings, threshold=0.92):
    """Check if an embedding is too similar to existing ones"""
    if not existing_embeddings:
        return False
        
    for emb_id, emb_vector in existing_embeddings.items():
        similarity = cosine_similarity(
            new_embedding.reshape(1, -1), 
            emb_vector.reshape(1, -1)
        )[0][0]
        
        if similarity > threshold:
            print(f"  Similar to existing embedding {emb_id} (similarity: {similarity:.4f})")
            return True
            
    return False

def verify_speaker_match(new_embedding, existing_embeddings, min_avg_confidence=0.60, min_max_confidence=0.75):
    """Verify if the new embedding matches the speaker with sufficient confidence using dual thresholds"""
    if not existing_embeddings:
        print("  No existing embeddings to verify against - cannot verify")
        return False, 0, 0
    
    # Calculate similarity with all existing embeddings
    similarities = []
    for emb_id, emb_vector in existing_embeddings.items():
        sim = cosine_similarity(
            new_embedding.reshape(1, -1), 
            emb_vector.reshape(1, -1)
        )[0][0]
        similarities.append(sim)
    
    # Calculate average and max similarity
    avg_similarity = np.mean(similarities)
    max_similarity = np.max(similarities)
    
    # Check against both thresholds
    passes_avg = avg_similarity >= min_avg_confidence
    passes_max = max_similarity >= min_max_confidence
    
    if passes_avg and passes_max:
        print(f"  ✅ Verified as speaker match: avg={avg_similarity:.4f}, max={max_similarity:.4f}")
        return True, avg_similarity, max_similarity
    else:
        fail_reason = []
        if not passes_avg:
            fail_reason.append(f"avg={avg_similarity:.4f} < {min_avg_confidence:.2f}")
        if not passes_max:
            fail_reason.append(f"max={max_similarity:.4f} < {min_max_confidence:.2f}")
            
        print(f"  ❌ Not verified: {', '.join(fail_reason)}")
        return False, avg_similarity, max_similarity

def add_speaker_embedding(speaker_name, audio_file, model, existing_embeddings, 
                         min_avg_confidence=0.60, min_max_confidence=0.75, dry_run=False):
    """Add a speaker embedding to Pinecone if verified and not a duplicate"""
    base_filename = os.path.basename(audio_file)
    print(f"Processing {base_filename}...")
    
    # Generate embedding
    embedding = model.get_embedding(audio_file)
    
    # Convert to numpy array
    if isinstance(embedding, torch.Tensor):
        embedding_np = embedding.squeeze().cpu().numpy()
    else:
        embedding_np = embedding.squeeze()
    
    # First check if this is a duplicate of an existing embedding
    if is_duplicate(embedding_np, existing_embeddings):
        print(f"  Skipping (duplicate embedding)")
        return None, "duplicate", base_filename
    
    # Verify the embedding matches the speaker
    is_match, avg_confidence, max_confidence = verify_speaker_match(
        embedding_np, existing_embeddings, 
        min_avg_confidence=min_avg_confidence,
        min_max_confidence=min_max_confidence
    )
    
    if not is_match and existing_embeddings:
        print(f"  Skipping (didn't verify as {speaker_name})")
        return None, "unverified", base_filename
    
    # Generate unique ID
    unique_id = f"speaker_{speaker_name}_{uuid.uuid4().hex[:8]}"
    
    # Convert to list for Pinecone
    embedding_list = embedding_np.tolist()
    
    # Create metadata
    metadata = {
        "speaker_name": speaker_name, 
        "source_file": base_filename,
        "avg_confidence": float(avg_confidence) if existing_embeddings else 1.0,
        "max_confidence": float(max_confidence) if existing_embeddings else 1.0
    }
    
    # Upload to Pinecone
    if not dry_run:
        index.upsert(vectors=[(unique_id, embedding_list, metadata)])
        print(f"  Added embedding with ID: {unique_id}" + 
              (f" (avg={avg_confidence:.4f}, max={max_confidence:.4f})" if existing_embeddings else " (first embedding)"))
        # Update local cache of embeddings
        existing_embeddings[unique_id] = embedding_np
    else:
        print(f"  Would add embedding with ID: {unique_id}" + 
              (f" (avg={avg_confidence:.4f}, max={max_confidence:.4f})" if existing_embeddings else " (first embedding)") + 
              " (dry run)")
    
    return unique_id, "added", base_filename

def process_speaker_folder(folder_path, speaker_name=None, 
                          min_avg_confidence=0.60, min_max_confidence=0.75, dry_run=False):
    """Process all utterances in a speaker folder"""
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"Error: Folder {folder_path} does not exist")
        return
    
    # Use folder name as speaker name if not provided
    if speaker_name is None:
        speaker_name = os.path.basename(folder_path)
    
    print(f"\nProcessing speaker: {speaker_name}")
    print(f"Using thresholds: min_avg_confidence={min_avg_confidence:.2f}, min_max_confidence={min_max_confidence:.2f}")
    
    # Load the speaker model
    print("Loading speaker recognition model...")
    model = EncDecSpeakerLabelModel.restore_from("models/titanet_large.nemo")
    
    # Get existing embeddings for this speaker
    print(f"Checking existing embeddings for {speaker_name}...")
    existing_embeddings = get_existing_embeddings(speaker_name)
    print(f"Found {len(existing_embeddings)} existing embeddings")
    
    # Find all WAV files in the folder
    wav_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.wav')]
    print(f"Found {len(wav_files)} WAV files in folder")
    
    # Process each WAV file
    added_count = 0
    skipped_duplicates = 0
    skipped_unverified = 0
    
    # Track files by status
    added_files = []
    duplicate_files = []
    unverified_files = []
    
    for wav_file in sorted(wav_files):
        file_path = os.path.join(folder_path, wav_file)
        result, status, filename = add_speaker_embedding(
            speaker_name, file_path, model, existing_embeddings, 
            min_avg_confidence=min_avg_confidence,
            min_max_confidence=min_max_confidence,
            dry_run=dry_run
        )
        
        if status == "added":
            added_count += 1
            added_files.append(filename)
        elif status == "duplicate":
            skipped_duplicates += 1
            duplicate_files.append(filename)
        elif status == "unverified":
            skipped_unverified += 1
            unverified_files.append(filename)
    
    print(f"\nSummary for {speaker_name}:")
    print(f"  ✅ Added: {added_count} new embeddings")
    print(f"  ⏭️ Skipped (duplicates): {skipped_duplicates}")
    print(f"  ❌ Skipped (unverified): {skipped_unverified}")
    
    # Print details of files not added
    if unverified_files:
        print("\nFiles that failed verification:")
        for i, file in enumerate(unverified_files, 1):
            print(f"  {i}. {file}")
    
    if dry_run and added_files:
        print("\nFiles that would be added (dry run):")
        for i, file in enumerate(added_files, 1):
            print(f"  {i}. {file}")
    
    return added_count, skipped_duplicates, skipped_unverified, added_files, unverified_files

def main():
    parser = argparse.ArgumentParser(description="Update speaker database with verified utterances")
    parser.add_argument("folder", help="Path to folder containing speaker utterances")
    parser.add_argument("--speaker", help="Speaker name (defaults to folder name)")
    parser.add_argument("--avg-confidence", type=float, default=0.60, 
                        help="Minimum average confidence threshold (0.0-1.0, default: 0.60)")
    parser.add_argument("--max-confidence", type=float, default=0.75, 
                        help="Minimum maximum confidence threshold (0.0-1.0, default: 0.75)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload to Pinecone")
    
    args = parser.parse_args()
    
    process_speaker_folder(
        args.folder, 
        args.speaker, 
        min_avg_confidence=args.avg_confidence,
        min_max_confidence=args.max_confidence,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main() 