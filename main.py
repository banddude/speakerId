from pinecone import Pinecone
import assemblyai as aai
import requests
import os
from pydub import AudioSegment
import mimetypes
import wave
from nemo.collections.asr.models import EncDecSpeakerLabelModel
import torch
import numpy as np
import uuid
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("speaker-embeddings")

# Initialize AssemblyAI
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def transcribe(file_path):
    """Transcribe a local audio file using AssemblyAI"""
    config = aai.TranscriptionConfig(speaker_labels=True)
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(file_path)
    return transcript.json_response

def convert_to_wav(input_file, output_dir="./content/converted_audio"):
    """Convert an audio file to WAV format"""
    os.makedirs(output_dir, exist_ok=True)
    
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    wav_filename = f"{base_filename}.wav"
    wav_file = os.path.join(output_dir, wav_filename)
    
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

def add_speaker_embedding_to_pinecone(speaker_name, speaker_embedding, unique_id=None):
    """Add a speaker embedding to Pinecone"""
    if isinstance(speaker_embedding, torch.Tensor):
        embedding_np = speaker_embedding.squeeze().cpu().numpy()
    elif isinstance(speaker_embedding, np.ndarray):
        embedding_np = speaker_embedding.squeeze()
    else:
        raise ValueError("Unsupported embedding type")

    if embedding_np.shape != (192,):
        raise ValueError(f"Expected embedding shape (192,), got {embedding_np.shape}")

    embedding_list = embedding_np.tolist()
    unique_id = unique_id or f"speaker_{speaker_name}_{uuid.uuid4().hex[:8]}"
    metadata = {"speaker_name": speaker_name}
    
    index.upsert(vectors=[(unique_id, embedding_list, metadata)])
    print(f"Added embedding for speaker {speaker_name} with ID {unique_id}")
    return unique_id

def find_closest_speaker(utterance_embedding, local_embeddings=None, local_only=False, threshold=0.5):
    """Find the closest matching speaker for an utterance"""
    def cosine_sim(a, b):
        return cosine_similarity(a.reshape(1, -1), b.reshape(1, -1))[0][0]

    best_match = {"speaker_name": "No match found", "score": 0}

    if local_embeddings is not None:
        for speaker_name, embedding in local_embeddings.items():
            score = cosine_sim(utterance_embedding, embedding)
            if score > best_match["score"]:
                print(f"Identified speaker {speaker_name} with confidence {score}")
                best_match = {"speaker_name": speaker_name, "score": score}

    if not local_only and (local_embeddings is None or len(local_embeddings) == 0):
        results = index.query(vector=utterance_embedding.tolist(), top_k=1, include_metadata=True)
        if results["matches"]:
            match = results["matches"][0]
            if match["score"] > best_match["score"]:
                best_match = {"speaker_name": match["metadata"]["speaker_name"], "score": match["score"]}

    return (best_match["speaker_name"], best_match["score"]) if best_match["score"] >= threshold else ("No match found", 0)

def identify_speakers_from_utterances(transcript, wav_file, min_utterance_length=5000, match_all_utterances=False):
    """Identify speakers in a transcript"""
    utterances = transcript["utterances"]
    speaker_model = EncDecSpeakerLabelModel.from_pretrained("nvidia/speakerverification_en_titanet_large")

    known_speakers = {}
    unknown_speakers = {}
    unknown_count = 0

    unknown_folder = "unknown_speaker_utterances"
    os.makedirs(unknown_folder, exist_ok=True)

    audio_file_name = os.path.basename(wav_file)
    full_audio = AudioSegment.from_wav(wav_file)

    def get_suitable_utterance(speaker, min_length):
        suitable = [u for u in utterances if u["speaker"] == speaker and (u["end"] - u["start"]) >= min_length]
        return max(suitable or [u for u in utterances if u["speaker"] == speaker], 
                  key=lambda u: u["end"] - u["start"])

    # First pass: Identify speakers
    for speaker in set(u["speaker"] for u in utterances):
        if speaker not in known_speakers and speaker not in unknown_speakers:
            utterance = get_suitable_utterance(speaker, min_utterance_length)
            
            start_ms = utterance["start"]
            end_ms = utterance["end"]
            utterance_audio = full_audio[start_ms:end_ms]
            
            temp_wav = "temp_utterance.wav"
            utterance_audio.export(temp_wav, format="wav")
            embedding = speaker_model.get_embedding(temp_wav)
            os.remove(temp_wav)
            
            speaker_name, score = find_closest_speaker(embedding)
            print(f"Speaker: {speaker}, Closest match: {speaker_name}, Score: {score}")
            
            if score > 0.5:
                known_speakers[speaker] = speaker_name
            else:
                unknown_count += 1
                unknown_name = f"Unknown Speaker {chr(64 + unknown_count)}"
                unknown_wav = f"{unknown_folder}/unknown_speaker_{unknown_count}_from_{audio_file_name}"
                utterance_audio.export(unknown_wav, format="wav")
                unknown_speakers[speaker] = {
                    "name": unknown_name,
                    "wav_file": unknown_wav,
                    "duration": end_ms - start_ms,
                }

    # Second pass: Replace speaker names
    for utterance in utterances:
        if utterance["speaker"] in known_speakers:
            utterance["speaker"] = known_speakers[utterance["speaker"]]
        elif utterance["speaker"] in unknown_speakers:
            utterance["speaker"] = unknown_speakers[utterance["speaker"]]["name"]

    # Third pass: Match all utterances if requested
    if match_all_utterances:
        print("Matching all utterances individually...")
        for utterance in utterances:
            start_ms = utterance["start"]
            end_ms = utterance["end"]
            utterance_audio = full_audio[start_ms:end_ms]
            
            temp_wav = "temp_utterance.wav"
            utterance_audio.export(temp_wav, format="wav")
            embedding = speaker_model.get_embedding(temp_wav)
            os.remove(temp_wav)
            
            new_speaker_name, score = find_closest_speaker(embedding)
            
            if score > 0.5 and new_speaker_name != utterance["speaker"]:
                print(f"Speaker change detected: '{utterance['speaker']}' -> '{new_speaker_name}' (Score: {score})")
                print(f"Utterance: {utterance['text'][:50]}...")
                utterance["speaker"] = new_speaker_name

    return utterances, unknown_speakers

def main():
    """Main function to demonstrate usage"""
    # Initialize the speaker recognition model
    speaker_model = EncDecSpeakerLabelModel.from_pretrained("nvidia/speakerverification_en_titanet_large")
    
    # Step 1: Add known speakers to the database
    print("Step 1: Adding known speakers to the database")
    known_speakers_dir = "known_speakers_wav"  # Changed from known_speakers to known_speakers_wav
    if os.path.exists(known_speakers_dir):
        for speaker_file in os.listdir(known_speakers_dir):
            if speaker_file.endswith('.wav'):  # Only look for WAV files
                speaker_name = os.path.splitext(speaker_file)[0]
                audio_path = os.path.join(known_speakers_dir, speaker_file)
                embedding = speaker_model.get_embedding(audio_path)  # No need to convert since it's already WAV
                add_speaker_embedding_to_pinecone(speaker_name, embedding)
    else:
        print(f"Please create a '{known_speakers_dir}' directory and add WAV files of known speakers")
        print("Format: speaker_name.wav")
        return

    # Step 2: Process conversation file
    print("\nStep 2: Processing conversation file")
    conversation_file = "conversation.wav"
    if not os.path.exists(conversation_file):
        print(f"Please add a conversation file named '{conversation_file}'")
        return

    # Convert and transcribe the conversation
    wav_file = convert_to_wav(conversation_file)
    transcript = transcribe(wav_file)
    
    # Identify speakers
    identified_utterances, unknown_speakers = identify_speakers_from_utterances(transcript, wav_file)
    
    # Print results
    print("\nTranscript with identified speakers:")
    for utterance in identified_utterances:
        print(f"{utterance['speaker']}: {utterance['text']}")
    
    if unknown_speakers:
        print("\nUnknown speakers detected:")
        for speaker, info in unknown_speakers.items():
            print(f"{info['name']} - Duration: {info['duration']/1000:.2f}s")
            print(f"Audio saved to: {info['wav_file']}")

if __name__ == "__main__":
    main()