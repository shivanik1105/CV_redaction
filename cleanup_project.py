"""
Clean up project by moving unnecessary files to archive folder.
Keeps only essential files for production.
"""
import os
import shutil
from pathlib import Path

# Files to KEEP (essential for production)
KEEP_FILES = {
    # Core application
    'app.py',
    'auth.py',
    'celery_app.py',
    'tasks.py',
    'redis_cache.py',
    'vector_search.py',
    'supabase_storage.py',
    
    # Pipeline components
    'cv_redaction_pipeline.py',
    'cv_intelligence_extractor.py',
    'universal_pipeline_engine.py',
    'llm_batch_processor.py',
    'filename_mapping_manager.py',
    
    # Configuration
    '.env',
    '.env.example',
    '.gitignore',
    'requirements.txt',
    'Procfile',
    'render.yaml',
    'runtime.txt',
    
    # Documentation (essential)
    'README.md',
    'CLAUDE.md',
    'WHATS_NEW.md',
    
    # Deployment guides
    'RAILWAY_DEPLOYMENT_GUIDE.md',
    'ORACLE_CLOUD_DEPLOYMENT_GUIDE.md',
    
    # Database setup
    'supabase_pgvector_setup.sql',
    'supabase_add_missing_columns.sql',
    'supabase_production_tables.sql',
    'create_embeddings_table.sql',
    
    # Utilities
    'regenerate_embeddings.py',
    'test_supabase_storage.py',
    'test_redis_cache.py',
}

# Folders to KEEP
KEEP_FOLDERS = {
    'templates',
    'static',
    'config',
    '.git',
    '.venv',
    '__pycache__',
    'uploads',
    'redacted_output',
    'llm_analysis',
}

# Files/folders to ARCHIVE (move to archive/)
ARCHIVE_PATTERNS = [
    # Test files
    'test_*.py',
    '*_test.py',
    'debug_*.py',
    'check_*.py',
    'validate_*.py',
    'quick_test.py',
    'concurrency_*.py',
    'focused_*.py',
    'mixed_*.py',
    
    # Build files
    'build_*.py',
    'build_*.ps1',
    'build_*.spec',
    '*.spec',
    
    # Temporary files
    '.tmp_*.py',
    '_probe_*.py',
    '_run_*.py',
    'tmp_*.py',
    
    # Log files
    '*.log',
    '*.err.log',
    '*.out.log',
    
    # Old documentation
    '*_SUMMARY.md',
    '*_COMPLETE.md',
    '*_READY.md',
    '*_DELIVERY.md',
    '*_RESULTS.md',
    '*_GUIDE.md' ,  # Keep only essential guides
    '*_EXPLAINED.md',
    '*_VISUAL.md',
    '*_REFERENCE.md',
    '*_STATUS.md',
    '*_CHECKLIST.md',
    '*_INSTRUCTIONS.md',
    '*_BREAKDOWN.md',
    '*_VERIFICATION.md',
    '*_CONFIRMED.md',
    '*_IMPLEMENTED.md',
    '*_SOLUTION.md',
    '*_ANALYSIS.md',
    
    # Old scripts
    'process_all_cvs_smart.py',
    'complete_remaining_cvs.py',
    'reset_and_process_all.py',
    'integrate_filename_mapping.py',
    'manage_filename_mappings.py',
    'cleanup_duplicates.py',
    'clean_supabase_data.py',
    'backfill_embeddings.py',
    'migrate_database.py',
    'update_frontend.py',
    'generate_synthetic_cv_benchmark.py',
    'run_quick_search_benchmark.py',
    
    # Deployment scripts (keep guides, archive scripts)
    'deploy_to_render.ps1',
    'push_to_github.ps1',
    'restart_app.ps1',
    
    # Old SQL
    'migration_*.sql',
    'supabase_rls_*.sql',
    'jd_library_schema.sql',
    'fix_pgvector_rpc.sql',
    'supabase_upload_jobs_table.sql',
    
    # Output files
    '*.txt',
    '*.json',
    '*.csv',
    
    # Docker (if not using)
    'Dockerfile',
    'docker-compose.yml',
    
    # Old GUI
    'cv_redactor_gui.py',
    'app_launcher.py',
    
    # Misc
    '.app_*',
    '.server_*',
    '.last_*',
    '.wait_*',
    '.upload_*',
    'e2e_*.json',
]

# Folders to ARCHIVE
ARCHIVE_FOLDERS = [
    'chatbot',
    'test_results',
    'samples',
    'debug_output',
    'final_output',
    'intelligence_output',
    'build',
    'dist',
    'release',
    '.claude-dev-helper',
    '.gradio',
    '.github',
    '.vscode',
]


def should_archive(path: Path) -> bool:
    """Check if file/folder should be archived."""
    name = path.name
    
    # Keep essential files
    if name in KEEP_FILES:
        return False
    
    # Keep essential folders
    if path.is_dir() and name in KEEP_FOLDERS:
        return False
    
    # Archive specific folders
    if path.is_dir() and name in ARCHIVE_FOLDERS:
        return True
    
    # Archive files matching patterns
    for pattern in ARCHIVE_PATTERNS:
        if path.match(pattern):
            return True
    
    return False


def cleanup_project():
    """Move unnecessary files to archive folder."""
    print("=" * 60)
    print("PROJECT CLEANUP")
    print("=" * 60)
    
    root = Path('.')
    archive = root / 'archive'
    archive.mkdir(exist_ok=True)
    
    archived_count = 0
    kept_count = 0
    
    # Process all files and folders
    for item in root.iterdir():
        # Skip archive folder itself
        if item.name == 'archive':
            continue
        
        if should_archive(item):
            try:
                dest = archive / item.name
                
                # If destination exists, add timestamp
                if dest.exists():
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dest = archive / f"{item.stem}_{timestamp}{item.suffix}"
                
                shutil.move(str(item), str(dest))
                print(f"✓ Archived: {item.name}")
                archived_count += 1
            except Exception as e:
                print(f"❌ Failed to archive {item.name}: {e}")
        else:
            kept_count += 1
    
    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"✓ Archived: {archived_count} items")
    print(f"✓ Kept: {kept_count} items")
    print(f"\n📁 Archived files moved to: {archive.absolute()}")
    
    print("\n" + "=" * 60)
    print("ESSENTIAL FILES REMAINING")
    print("=" * 60)
    
    # List remaining files
    remaining = sorted([f.name for f in root.iterdir() if f.is_file() and f.name != 'cleanup_project.py'])
    for i, name in enumerate(remaining[:20], 1):
        print(f"  {i}. {name}")
    
    if len(remaining) > 20:
        print(f"  ... and {len(remaining) - 20} more files")
    
    print("\n✅ Project cleanup complete!")
    print("   Your project is now cleaner and easier to navigate.")


if __name__ == "__main__":
    try:
        cleanup_project()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()

