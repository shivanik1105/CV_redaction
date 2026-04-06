"""
Cleanup Duplicate Intelligence Files
Keeps only the most recent intelligence file for each CV
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def cleanup_duplicate_intelligence_files():
    """Remove duplicate intelligence files, keeping only the most recent for each CV"""
    
    intelligence_dir = Path('llm_analysis')
    
    # Group files by original CV filename
    cv_files = defaultdict(list)
    
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get original filename
            orig_file = data.get('original_filename_raw', '')
            if not orig_file:
                continue
            
            # Get timestamp from intelligence file
            timestamp_str = data.get('extraction_timestamp') or data.get('analysis_date', '')
            
            cv_files[orig_file].append({
                'path': json_file,
                'timestamp': timestamp_str,
                'data': data
            })
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")
    
    # Find and remove duplicates
    total_files = 0
    duplicates_removed = 0
    
    for orig_file, files in cv_files.items():
        total_files += len(files)
        
        if len(files) > 1:
            # Sort by timestamp (most recent first)
            files.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Keep the most recent, delete the rest
            keep_file = files[0]
            duplicate_files = files[1:]
            
            print(f"\n{orig_file}:")
            print(f"  Keeping: {keep_file['path'].name} ({keep_file['timestamp']})")
            
            for dup in duplicate_files:
                print(f"  Deleting: {dup['path'].name} ({dup['timestamp']})")
                dup['path'].unlink()
                duplicates_removed += 1
    
    print(f"\n{'='*60}")
    print(f"Cleanup Complete")
    print(f"{'='*60}")
    print(f"Total intelligence files: {total_files}")
    print(f"Unique CVs: {len(cv_files)}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Files remaining: {total_files - duplicates_removed}")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("CV Intelligence Duplicate Cleanup")
    print("="*60)
    print("This will remove duplicate intelligence files,")
    print("keeping only the most recent analysis for each CV.")
    print("="*60)
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        cleanup_duplicate_intelligence_files()
    else:
        print("Cancelled.")
