#!/usr/bin/env python3
"""
Script to rename a speaker in a processed conversation.
This updates:
- The speaker directory name
- All metadata.json entries
- Both transcript files

And optionally runs the update_speaker_db_verified.py script for the renamed speaker.
"""

import os
import sys
import json
import shutil
import re
import subprocess
from pathlib import Path

def rename_speaker(conversation_path, old_speaker, new_speaker, update_db=False, confidence_threshold=0.60):
    """
    Rename a speaker in a processed conversation and update all related files.
    
    Args:
        conversation_path: Path to the conversation directory
        old_speaker: Current speaker name to replace
        new_speaker: New speaker name
        update_db: Whether to run the update_speaker_db_verified.py script after renaming
        confidence_threshold: Confidence threshold for the update_speaker_db_verified.py script
    """
    # Normalize path
    conversation_path = os.path.abspath(conversation_path)
    
    if not os.path.isdir(conversation_path):
        print(f"Error: {conversation_path} is not a valid directory")
        return False
    
    print(f"Renaming speaker '{old_speaker}' to '{new_speaker}' in {conversation_path}")
    
    # Check if this is a valid conversation directory
    metadata_path = os.path.join(conversation_path, "metadata.json")
    if not os.path.exists(metadata_path):
        print(f"Error: {conversation_path} does not contain metadata.json")
        return False
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Check if old speaker exists in the metadata
    if old_speaker not in metadata["speakers"]:
        print(f"Error: Speaker '{old_speaker}' not found in metadata")
        return False
    
    # Create normalized directory names
    old_speaker_dir_name = old_speaker.replace(" ", "_")
    new_speaker_dir_name = new_speaker.replace(" ", "_")
    
    # Check if the speaker directory exists
    speakers_dir = os.path.join(conversation_path, "speakers")
    old_speaker_dir = os.path.join(speakers_dir, old_speaker_dir_name)
    new_speaker_dir = os.path.join(speakers_dir, new_speaker_dir_name)
    
    if not os.path.isdir(old_speaker_dir):
        print(f"Error: Speaker directory '{old_speaker_dir}' not found")
        return False
    
    if os.path.exists(new_speaker_dir) and old_speaker_dir_name != new_speaker_dir_name:
        print(f"Error: Directory '{new_speaker_dir}' already exists")
        return False
    
    # Now let's make the changes
    changes_made = 0
    
    # Calculate project directory (two levels up from conversation dir)
    project_dir = Path(conversation_path).parent.parent
    
    # 1. Rename the speaker directory
    if old_speaker_dir_name != new_speaker_dir_name:
        print(f"Renaming directory: {old_speaker_dir} -> {new_speaker_dir}")
        os.rename(old_speaker_dir, new_speaker_dir)
        changes_made += 1
    
    # 2. Update metadata.json
    # Replace in speakers list
    if old_speaker in metadata["speakers"]:
        metadata["speakers"] = [new_speaker if s == old_speaker else s for s in metadata["speakers"]]
        changes_made += 1
    
    # Replace in utterances
    for utterance in metadata["utterances"]:
        if utterance["speaker"] == old_speaker:
            utterance["speaker"] = new_speaker
            changes_made += 1
    
    # Save updated metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # 3. Update transcript file in the conversation directory
    transcript_path = os.path.join(conversation_path, "transcript.txt")
    if os.path.exists(transcript_path):
        with open(transcript_path, 'r') as f:
            transcript_content = f.read()
        
        # Replace [Old Speaker ... with [New Speaker ...
        pattern = r'\[' + re.escape(old_speaker) + r' ([0-9:]{8})'
        replacement = '[' + new_speaker + r' \1'
        updated_content = re.sub(pattern, replacement, transcript_content)
        
        if updated_content != transcript_content:
            with open(transcript_path, 'w') as f:
                f.write(updated_content)
            changes_made += 1
            print(f"Updated transcript file: {transcript_path}")
    
    # 4. Find and update the legacy transcript file in the main directory
    # Legacy transcripts have format: transcript_YYYYMMDD_HHMMSS.txt
    # Extract conversation ID to help find the right legacy transcript
    conversation_id = os.path.basename(conversation_path)
    
    # Metadata contains date_processed which can help identify the right legacy transcript
    if "date_processed" in metadata:
        # Extract date from ISO format string (2025-03-12T...)
        date_parts = metadata["date_processed"].split("T")[0].split("-")
        if len(date_parts) == 3:
            date_prefix = f"{date_parts[0]}{date_parts[1]}{date_parts[2]}"
            
            # Look for legacy transcripts with this date prefix
            legacy_transcripts = list(project_dir.glob(f"transcript_{date_prefix}_*.txt"))
            
            for legacy_path in legacy_transcripts:
                # Read the transcript to check if it contains the old speaker name
                with open(legacy_path, 'r') as f:
                    legacy_content = f.read()
                
                # Look for lines that start with "Old Speaker: "
                pattern = r'^' + re.escape(old_speaker) + r': '
                replacement = new_speaker + ': '
                
                updated_legacy = re.sub(pattern, replacement, legacy_content, flags=re.MULTILINE)
                
                if updated_legacy != legacy_content:
                    with open(legacy_path, 'w') as f:
                        f.write(updated_legacy)
                    changes_made += 1
                    print(f"Updated legacy transcript: {legacy_path}")
    
    # 5. Update any symlinks within the speaker directories
    # This is only necessary if we're on a system that supports symlinks
    # and the speaker_id_testing.py script used symlinks rather than copies
    
    # Move any files from the legacy speaker_utterances directory
    legacy_speaker_dir = os.path.join(project_dir, "speaker_utterances", old_speaker)
    new_legacy_speaker_dir = os.path.join(project_dir, "speaker_utterances", new_speaker)
    
    if os.path.exists(legacy_speaker_dir):
        print(f"Moving files from legacy directory: {legacy_speaker_dir} -> {new_legacy_speaker_dir}")
        
        if not os.path.exists(new_legacy_speaker_dir):
            os.makedirs(new_legacy_speaker_dir, exist_ok=True)
        
        # Move all files
        for item in os.listdir(legacy_speaker_dir):
            old_path = os.path.join(legacy_speaker_dir, item)
            new_path = os.path.join(new_legacy_speaker_dir, item)
            
            if os.path.exists(new_path):
                if os.path.isfile(new_path):
                    os.remove(new_path)
            
            shutil.move(old_path, new_path)
            changes_made += 1
        
        # Remove old directory if empty
        if len(os.listdir(legacy_speaker_dir)) == 0:
            os.rmdir(legacy_speaker_dir)
            print(f"Removed empty legacy directory: {legacy_speaker_dir}")
    
    # Print summary
    print(f"\nRename operation completed with {changes_made} changes:")
    print(f"- Speaker '{old_speaker}' has been renamed to '{new_speaker}'")
    print(f"- Directory: {speakers_dir}/{old_speaker_dir_name} -> {speakers_dir}/{new_speaker_dir_name}")
    print(f"- Metadata and transcripts have been updated")
    
    # 6. Run update_speaker_db_verified.py if requested
    if update_db:
        # Check if the legacy speaker directory exists (it should after the rename operation)
        target_dir = os.path.join("speaker_utterances", new_speaker)
        if os.path.isdir(os.path.join(project_dir, target_dir)):
            print(f"\nRunning update_speaker_db_verified.py for {new_speaker}...")
            command = [
                "python", 
                "update_speaker_db_verified.py", 
                target_dir, 
                "--avg-confidence", 
                str(confidence_threshold)
            ]
            
            try:
                # Run the update command
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                print(result.stdout)
                print(f"Successfully updated database for {new_speaker}")
            except subprocess.CalledProcessError as e:
                print(f"Error updating database: {e}")
                print(f"Output: {e.stdout}")
                print(f"Error: {e.stderr}")
        else:
            print(f"Warning: Could not find speaker directory '{target_dir}' for database update")
    
    return True

def main():
    """Process command line arguments and execute the rename operation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rename a speaker in a processed conversation.")
    parser.add_argument("conversation_path", help="Path to the conversation directory")
    parser.add_argument("old_speaker", help="Current speaker name to replace")
    parser.add_argument("new_speaker", help="New speaker name")
    parser.add_argument("--update-db", action="store_true", help="Run update_speaker_db_verified.py after renaming")
    parser.add_argument("--confidence", type=float, default=0.60, help="Confidence threshold for update_speaker_db_verified.py")
    
    args = parser.parse_args()
    
    success = rename_speaker(
        args.conversation_path, 
        args.old_speaker, 
        args.new_speaker, 
        update_db=args.update_db,
        confidence_threshold=args.confidence
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 