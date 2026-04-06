"""
Quick Progress Checker
Shows how many CVs have been processed so far
"""
from pathlib import Path
import json
import re


def _all_source_cv_names() -> set:
    names = set()
    for folder in [Path('samples'), Path('samples/more')]:
        if not folder.exists():
            continue
        for ext in ['*.pdf', '*.docx', '*.doc']:
            for f in folder.glob(ext):
                names.add(f.name)
    return names


def _extract_original_filename_from_json_path(json_file: Path) -> str:
    stem = json_file.stem
    suffix = '_intelligence'
    if stem.endswith(suffix):
        core = stem[:-len(suffix)]
    else:
        core = stem

    match = re.match(r'^REDACTED_\d{8}_\d{6}_(.+)$', core)
    if match:
        remaining = match.group(1)
        if remaining.endswith('.txt'):
            remaining = remaining[:-4]
        return remaining
    return ''


def _processed_source_cv_names(source_names: set) -> set:
    intelligence_dir = Path('llm_analysis')
    processed_names = set()
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)

            raw_name = data.get('original_filename_raw')
            if raw_name:
                candidate_name = Path(raw_name).name
                if candidate_name in source_names:
                    processed_names.add(candidate_name)

            fallback_name = data.get('original_filename')
            if fallback_name:
                candidate_name = Path(fallback_name).name
                if candidate_name in source_names:
                    processed_names.add(candidate_name)

            inferred = _extract_original_filename_from_json_path(json_file)
            if inferred in source_names:
                processed_names.add(inferred)
        except Exception:
            continue
    return processed_names

def check_progress():
    # Count original CVs
    source_names = _all_source_cv_names()
    total_cvs = len(source_names)
    
    # Count processed intelligence files
    processed_names = _processed_source_cv_names(source_names)
    processed = len(processed_names)
    
    # Count redacted files
    redacted_dir = Path('redacted_output')
    redacted = len(list(redacted_dir.glob('REDACTED_*.txt')))
    
    print("="*60)
    print("CV PROCESSING PROGRESS")
    print("="*60)
    print(f"Total CVs to process: {total_cvs}")
    redacted_pct = (redacted / total_cvs * 100) if total_cvs else 0
    analyzed_pct = (processed / total_cvs * 100) if total_cvs else 0
    print(f"Redacted: {redacted}/{total_cvs} ({redacted_pct:.1f}%)")
    print(f"Analyzed: {processed}/{total_cvs} ({analyzed_pct:.1f}%)")
    print("="*60)
    
    if processed < total_cvs:
        print(f"⏳ Still processing... {total_cvs - processed} remaining")
    else:
        print("✓ All CVs processed!")
    
    # Show last 3 processed
    if processed > 0:
        print("\nLast 3 processed:")
        intelligence_dir = Path('llm_analysis')
        intelligence_files = sorted(intelligence_dir.glob('*_intelligence.json'), 
                                   key=lambda x: x.stat().st_mtime, reverse=True)
        for i, f in enumerate(intelligence_files[:3], 1):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                anon_id = data.get('anonymized_id', 'UNKNOWN')
                verdict = data.get('verdict') or 'EXTRACTED'
                print(f"  {i}. {anon_id} - {verdict}")
            except:
                pass

if __name__ == '__main__':
    check_progress()
