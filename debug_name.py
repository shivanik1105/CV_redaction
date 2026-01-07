
import re
import os

def _extract_names_from_filename(filename: str):
    basename = os.path.basename(filename)
    # Remove extension
    root, _ = os.path.splitext(basename)
    # Clean non-alpha characters (like [ or digits)
    # The existing logic (from memory) might be:
    # re.sub(r'[^a-zA-Z\s]', ' ', root)
    
    # Let's simulate what's in the current file
    clean_root = re.sub(r'[^a-zA-Z\s]', ' ', root)
    
    # CamelCase split
    splitted = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_root)
    
    parts = splitted.split()
    potential_names = []
    
    # Original logic roughly:
    if len(parts) >= 2:
        full_name = " ".join(parts)
        potential_names.append(full_name) # "Abhishek Kumar Dwivedi"
        
        # Also add permutations? No, just the full name.
    
    print(f"Filename: {filename}")
    print(f"Root: {root}")
    print(f"Clean Root: {clean_root}")
    print(f"Splitted: {splitted}")
    print(f"Parts: {parts}")
    print(f"Potential Names: {potential_names}")

_extract_names_from_filename("AbhishekKumarDwivedi[.pdf")
