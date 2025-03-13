#!/usr/bin/env python3
# Script to add short utterances to the Pinecone database

import os
import uuid
from pinecone import Pinecone
from nemo.collections.asr.models import EncDecSpeakerLabelModel
import numpy as np
import torch

# Set custom HuggingFace cache directory in the project folder
os.environ["TRANSFORMERS_CACHE"] = os.path.join(os.getcwd(), "hf_cache")
os.environ["HF_HOME"] = os.path.join(os.getcwd(), "hf_cache")
os.makedirs(os.path.join(os.getcwd(), "hf_cache"), exist_ok=True)

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("speaker-embeddings")

# Short utterances for Mike Shaffer
mike_short_files = [
    "processed_conversations/conversation_20250312_154532/speakers/Mike_Shaffer/utterance_015.wav",
    "processed_conversations/conversation_20250312_154532/speakers/Mike_Shaffer/utterance_143.wav",
    "processed_conversations/conversation_20250312_154532/speakers/Mike_Shaffer/utterance_007.wav",
    "processed_conversations/conversation_20250312_154532/speakers/Mike_Shaffer/utterance_011.wav"
]

# Short utterances for Simeon Reyes
simeon_short_files = [
    "processed_conversations/conversation_20250312_154532/speakers/Simeon_Reyes/utterance_050.wav",
    "processed_conversations/conversation_20250312_154532/speakers/Simeon_Reyes/utterance_066.wav",
    "processed_conversations/conversation_20250312_154532/speakers/Simeon_Reyes/utterance_056.wav",
    "processed_conversations/conversation_20250312_154532/speakers/Simeon_Reyes/utterance_128.wav"
]

def add_utterance_to_pinecone(audio_file, speaker_name):
    """Add a short utterance to the Pinecone database"""
    print(f"Processing {audio_file}...")
    
    # Load the speaker recognition model
    model_path = "models/titanet_large.nemo"
    speaker_model = EncDecSpeakerLabelModel.restore_from(model_path)
    
    # Generate embedding
    embedding = speaker_model.get_embedding(audio_file)
    
    # Convert to numpy array
    if isinstance(embedding, torch.Tensor):
        embedding_np = embedding.squeeze().cpu().numpy()
    else:
        embedding_np = embedding.squeeze()
    
    # Generate unique ID
    unique_id = f"speaker_{speaker_name.replace(' ', '_')}_short_{uuid.uuid4().hex[:8]}"
    
    # Convert to list for Pinecone
    embedding_list = embedding_np.tolist()
    
    # Create metadata with special flag for short utterance
    metadata = {
        "speaker_name": speaker_name,
        "source_file": os.path.basename(audio_file),
        "is_short_utterance": True
    }
    
    # Upload to Pinecone
    index.upsert(vectors=[(unique_id, embedding_list, metadata)])
    print(f"  Added embedding with ID: {unique_id}")
    
    return unique_id

# Add Mike's short utterances
print("\nAdding short utterances for Mike Shaffer...")
for file in mike_short_files:
    add_utterance_to_pinecone(file, "Mike Shaffer")

# Add Simeon's short utterances
print("\nAdding short utterances for Simeon Reyes...")
for file in simeon_short_files:
    add_utterance_to_pinecone(file, "Simeon Reyes")

print("\nFinished adding short utterances to the database.") 