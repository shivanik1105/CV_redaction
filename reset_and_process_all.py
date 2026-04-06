"""
Reset Everything and Process All CVs from Scratch
"""
import os
import shutil
from pathlib import Path

def reset_all_data():
    """Delete all processed data to start fresh"""
    
    print("="*80)
    print("RESET AND CLEAN ALL DATA")
    print("="*80)
    print("\nThis will delete:")
    print("  - All redacted CVs (redacted_output/)")
    print("  - All intelligence files (llm_analysis/)")
    print("  - All final output (final_output/)")
    print("\nOriginal CVs in samples/ will NOT be deleted.")
    print("="*80)
    
    response = input("\nAre you sure? Type 'yes' to continue: ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return False
    
    # Directories to clean
    dirs_to_clean = [
        'redacted_output',
        'llm_analysis',
        'final_output',
        'debug_output'
    ]
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            file_count = len(list(dir_path.glob('*')))
            print(f"\nDeleting {file_count} files from {dir_name}/...")
            
            for file in dir_path.glob('*'):
                if file.is_file():
                    file.unlink()
            
            print(f"  ✓ Cleaned {dir_name}/")
        else:
            print(f"  - {dir_name}/ doesn't exist, skipping")
    
    print("\n" + "="*80)
    print("✓ All processed data deleted!")
    print("="*80)
    return True


if __name__ == '__main__':
    if reset_all_data():
        print("\n" + "="*80)
        print("READY TO PROCESS")
        print("="*80)
        print("\nNow run:")
        print("  python process_all_cvs_smart.py --max 100")
        print("\nThis will process all 75 CVs in extraction-only mode (no JD required).")
        print("="*80)
