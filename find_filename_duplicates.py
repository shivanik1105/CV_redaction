"""
Find duplicate CVs based on filename patterns and content similarity.
This catches duplicates that the hash-based checker misses.
"""
from supabase_storage import SupabaseStorage
from collections import defaultdict
import re
from difflib import SequenceMatcher

def extract_name_from_filename(filename: str) -> str:
    """Extract the person's name from various filename formats."""
    if not filename:
        return ""
    
    # Remove common prefixes and timestamps
    name = re.sub(r'^\d{8}_\d{6}_', '', filename)  # Remove timestamp prefix
    name = re.sub(r'^\d{8}_', '', name)  # Remove date prefix
    name = re.sub(r'^REDACTED_', '', name, flags=re.IGNORECASE)
    
    # Remove file extensions
    name = re.sub(r'\.(pdf|docx|doc)$', '', name, flags=re.IGNORECASE)
    
    # Extract name patterns
    # Pattern 1: "Resume_-Name" or "Resume-Name"
    match = re.search(r'Resume[_-]+([A-Za-z]+(?:[_\s][A-Za-z]+)*)', name, re.IGNORECASE)
    if match:
        return match.group(1).replace('_', ' ').strip().lower()
    
    # Pattern 2: "Naukri_NameExperience" (e.g., "Naukri_MayurPatil3y_2m")
    match = re.search(r'Naukri[_-]+([A-Za-z]+(?:[A-Z][a-z]+)*)', name, re.IGNORECASE)
    if match:
        # Split camelCase
        name_part = match.group(1)
        name_part = re.sub(r'([a-z])([A-Z])', r'\1 \2', name_part)
        name_part = re.sub(r'\d.*$', '', name_part)  # Remove experience part
        return name_part.strip().lower()
    
    # Pattern 3: Just the name with underscores
    name = re.sub(r'[_-]+', ' ', name)
    name = re.sub(r'\d+', '', name)  # Remove numbers
    name = re.sub(r'\s+', ' ', name).strip().lower()
    
    return name

def similarity_score(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (0-1)."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def find_filename_duplicates():
    """Find duplicates based on filename patterns."""
    print("=" * 80)
    print("FILENAME-BASED DUPLICATE DETECTION")
    print("=" * 80)
    
    storage = SupabaseStorage()
    
    # Get all candidates with their filenames
    print("\nFetching all candidates with filenames...")
    
    # Get from cv_intelligence
    intel_response = storage.client.table('cv_intelligence').select(
        'anonymized_id, created_at, years_experience, primary_domain, core_technical_skills'
    ).execute()
    
    # Get from cv_filename_mapping
    mapping_response = storage.client.table('cv_filename_mapping').select(
        'anonymized_id, original_filename, anonymized_filename'
    ).execute()
    
    # Create mapping dict
    filename_map = {
        m['anonymized_id']: {
            'original': m.get('original_filename', ''),
            'anonymized': m.get('anonymized_filename', '')
        }
        for m in mapping_response.data
    }
    
    # Combine data
    candidates = []
    for intel in intel_response.data:
        anon_id = intel['anonymized_id']
        filenames = filename_map.get(anon_id, {'original': '', 'anonymized': ''})
        
        candidates.append({
            'anonymized_id': anon_id,
            'created_at': intel.get('created_at', ''),
            'original_filename': filenames['original'],
            'anonymized_filename': filenames['anonymized'],
            'years_experience': intel.get('years_experience', 0),
            'primary_domain': intel.get('primary_domain', ''),
            'core_skills': intel.get('core_technical_skills', [])
        })
    
    print(f"✓ Found {len(candidates)} total candidates")
    
    # Group by extracted name
    name_groups = defaultdict(list)
    no_filename_count = 0
    
    for cand in candidates:
        filename = cand['original_filename'] or cand['anonymized_filename']
        
        if not filename:
            no_filename_count += 1
            continue
        
        extracted_name = extract_name_from_filename(filename)
        
        if extracted_name and len(extracted_name) > 3:  # Ignore very short names
            name_groups[extracted_name].append(cand)
    
    # Find potential duplicates
    duplicates = {name: cands for name, cands in name_groups.items() if len(cands) > 1}
    
    print(f"\n📊 Analysis:")
    print(f"   Unique names extracted: {len(name_groups)}")
    print(f"   Candidates without filename: {no_filename_count}")
    print(f"   Potential duplicate groups: {len(duplicates)}")
    
    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} groups of potential duplicates:\n")
        
        total_duplicates = 0
        confirmed_duplicates = []
        
        for i, (name, cands) in enumerate(sorted(duplicates.items()), 1):
            # Sort by creation date
            cands_sorted = sorted(cands, key=lambda x: x.get('created_at', ''))
            
            print(f"  Group {i}: '{name}' ({len(cands)} candidates)")
            
            for j, cand in enumerate(cands_sorted):
                marker = "KEEP" if j == 0 else "DELETE?"
                created = cand.get('created_at', 'unknown')[:19]
                filename = cand['original_filename'] or cand['anonymized_filename']
                years = cand.get('years_experience', 'N/A')
                domain = (cand.get('primary_domain') or 'N/A')[:40]
                
                print(f"    [{marker}] {cand['anonymized_id']}")
                print(f"            File: {filename}")
                print(f"            Created: {created} | Exp: {years} yrs | Domain: {domain}")
            
            print()
            
            # Check if they're truly duplicates (same experience, domain, skills)
            if len(cands) > 1:
                first = cands_sorted[0]
                are_duplicates = True
                
                for cand in cands_sorted[1:]:
                    # Compare key attributes
                    exp_match = abs(float(first.get('years_experience', 0) or 0) - 
                                   float(cand.get('years_experience', 0) or 0)) < 1
                    domain_match = similarity_score(
                        first.get('primary_domain', ''),
                        cand.get('primary_domain', '')
                    ) > 0.7
                    
                    if exp_match and domain_match:
                        confirmed_duplicates.append(cand['anonymized_id'])
                    else:
                        are_duplicates = False
                
                if are_duplicates:
                    total_duplicates += len(cands) - 1
                    print(f"    ✓ CONFIRMED DUPLICATES (same experience & domain)")
                else:
                    print(f"    ⚠ POSSIBLE DUPLICATES (different experience/domain - might be different people)")
                print()
        
        print(f"{'='*80}")
        print(f"📊 Summary:")
        print(f"   Total candidates: {len(candidates)}")
        print(f"   Confirmed duplicates to remove: {total_duplicates}")
        print(f"   After cleanup: {len(candidates) - total_duplicates}")
        print(f"{'='*80}")
        
        if total_duplicates > 0:
            print(f"\n⚠️  Do you want to delete {total_duplicates} confirmed duplicate candidates?")
            print("   (This will keep the oldest upload of each CV)")
            response = input("   Delete duplicates? (yes/no): ").strip().lower()
            
            if response == 'yes':
                delete_confirmed_duplicates(storage, confirmed_duplicates)
            else:
                print("\n❌ Cleanup cancelled. No changes made.")
        else:
            print("\n✓ No confirmed duplicates found (candidates with same name have different experience/domain)")
    else:
        print("\n✅ No duplicate filenames found! All candidates have unique names.")
    
    return 0

def delete_confirmed_duplicates(storage, duplicate_ids):
    """Delete confirmed duplicate candidates."""
    print("\n" + "=" * 80)
    print("DELETING CONFIRMED DUPLICATES")
    print("=" * 80)
    
    deleted_count = 0
    error_count = 0
    
    for anon_id in duplicate_ids:
        try:
            # Delete in correct order to avoid FK constraint errors
            # 1. cv_filename_mapping first
            try:
                storage.client.table('cv_filename_mapping').delete().eq(
                    'anonymized_id', anon_id
                ).execute()
            except Exception:
                pass
            
            # 2. cv_embeddings
            try:
                storage.client.table('cv_embeddings').delete().eq(
                    'anonymized_id', anon_id
                ).execute()
            except Exception:
                pass
            
            # 3. cv_intelligence (parent table)
            storage.client.table('cv_intelligence').delete().eq(
                'anonymized_id', anon_id
            ).execute()
            
            print(f"  ✓ Deleted: {anon_id}")
            deleted_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to delete {anon_id}: {e}")
            error_count += 1
    
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"✓ Deleted: {deleted_count} duplicates")
    print(f"❌ Errors: {error_count}")
    
    if deleted_count > 0:
        print("\n🎉 Duplicate cleanup complete!")
        print("   Your database now contains only unique candidates.")

if __name__ == "__main__":
    try:
        find_filename_duplicates()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
