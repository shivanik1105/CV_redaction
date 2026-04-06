#!/usr/bin/env python3
"""
Filename Mapping Management CLI
Utility to view, search, sync, and export filename mappings
"""
import argparse
import sys
from pathlib import Path
from filename_mapping_manager import FilenameMappingManager

# Optional Supabase support
try:
    from supabase_storage import SupabaseStorage
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


def get_storage():
    """Get Supabase storage if available"""
    if SUPABASE_AVAILABLE:
        try:
            return SupabaseStorage()
        except Exception as e:
            print(f"⚠️  Supabase not available: {e}")
    return None


def cmd_list(args):
    """List all filename mappings"""
    manager = FilenameMappingManager()
    storage = get_storage() if not args.local_only else None
    
    mappings = manager.get_all_mappings(storage)
    
    if not mappings:
        print("No mappings found")
        return
    
    print(f"\n{'Anonymized ID':<15} {'Original Filename':<40} {'Anonymized Filename':<40}")
    print("=" * 100)
    
    for mapping in mappings:
        anon_id = mapping.get('anonymized_id', 'N/A')
        original = mapping.get('original_filename', 'N/A')
        anonymized = mapping.get('anonymized_filename', 'N/A')
        print(f"{anon_id:<15} {original:<40} {anonymized:<40}")
    
    print(f"\nTotal: {len(mappings)} mappings")


def cmd_lookup(args):
    """Lookup a specific mapping"""
    manager = FilenameMappingManager()
    storage = get_storage() if not args.local_only else None
    
    if args.anonymized_id:
        mapping = manager.get_mapping(args.anonymized_id, storage)
        if mapping:
            print(f"\nAnonymized ID: {args.anonymized_id}")
            print(f"Original Filename: {mapping.get('original_filename')}")
            print(f"Anonymized Filename: {mapping.get('anonymized_filename')}")
            if 'created_at' in mapping:
                print(f"Created: {mapping.get('created_at')}")
        else:
            print(f"❌ No mapping found for: {args.anonymized_id}")
    
    elif args.original_filename:
        anon_id = manager.reverse_lookup_by_original(args.original_filename, storage)
        if anon_id:
            print(f"\nOriginal Filename: {args.original_filename}")
            print(f"Anonymized ID: {anon_id}")
            
            # Get full mapping
            mapping = manager.get_mapping(anon_id, storage)
            if mapping:
                print(f"Anonymized Filename: {mapping.get('anonymized_filename')}")
        else:
            print(f"❌ No mapping found for: {args.original_filename}")


def cmd_sync(args):
    """Sync mappings from intelligence files"""
    manager = FilenameMappingManager()
    
    print("Syncing mappings from intelligence files...")
    result = manager.sync_from_intelligence_files(args.intelligence_folder)
    
    print(f"\n✓ Sync complete:")
    print(f"  - Synced: {result['synced']}")
    print(f"  - Skipped: {result['skipped']}")
    print(f"  - Errors: {result['errors']}")
    print(f"  - Total mappings: {result['total_mappings']}")


def cmd_export(args):
    """Export mappings to CSV"""
    manager = FilenameMappingManager()
    storage = get_storage() if not args.local_only else None
    
    print(f"Exporting mappings to {args.output}...")
    manager.export_mappings_csv(args.output, storage)
    print(f"✓ Export complete: {args.output}")


def cmd_stats(args):
    """Show mapping statistics"""
    manager = FilenameMappingManager()
    storage = get_storage() if not args.local_only else None
    
    mappings = manager.get_all_mappings(storage)
    
    print(f"\nFilename Mapping Statistics")
    print("=" * 50)
    print(f"Total mappings: {len(mappings)}")
    
    if mappings:
        # Count unique original filenames
        original_files = set(m.get('original_filename') for m in mappings if m.get('original_filename'))
        print(f"Unique original files: {len(original_files)}")
        
        # Count unique anonymized filenames
        anon_files = set(m.get('anonymized_filename') for m in mappings if m.get('anonymized_filename'))
        print(f"Unique anonymized files: {len(anon_files)}")
    
    # Check storage sources
    if SUPABASE_AVAILABLE and storage:
        print(f"\nStorage: Supabase + Local JSON")
    else:
        print(f"\nStorage: Local JSON only")
    
    print(f"Local file: {manager.local_mapping_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage CV filename mappings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all mappings
  python manage_filename_mappings.py list
  
  # Lookup by anonymized ID
  python manage_filename_mappings.py lookup --id CAND_882
  
  # Lookup by original filename
  python manage_filename_mappings.py lookup --original "John_Doe_CV.pdf"
  
  # Sync from intelligence files
  python manage_filename_mappings.py sync
  
  # Export to CSV
  python manage_filename_mappings.py export --output mappings.csv
  
  # Show statistics
  python manage_filename_mappings.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all mappings')
    list_parser.add_argument('--local-only', action='store_true', help='Use local storage only')
    
    # Lookup command
    lookup_parser = subparsers.add_parser('lookup', help='Lookup a specific mapping')
    lookup_group = lookup_parser.add_mutually_exclusive_group(required=True)
    lookup_group.add_argument('--id', dest='anonymized_id', help='Anonymized ID (e.g., CAND_882)')
    lookup_group.add_argument('--original', dest='original_filename', help='Original filename')
    lookup_parser.add_argument('--local-only', action='store_true', help='Use local storage only')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync mappings from intelligence files')
    sync_parser.add_argument('--intelligence-folder', default='llm_analysis', help='Intelligence folder path')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export mappings to CSV')
    export_parser.add_argument('--output', default='filename_mappings.csv', help='Output CSV file')
    export_parser.add_argument('--local-only', action='store_true', help='Use local storage only')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show mapping statistics')
    stats_parser.add_argument('--local-only', action='store_true', help='Use local storage only')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    commands = {
        'list': cmd_list,
        'lookup': cmd_lookup,
        'sync': cmd_sync,
        'export': cmd_export,
        'stats': cmd_stats
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
