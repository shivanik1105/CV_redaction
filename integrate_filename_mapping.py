"""
Integration Example: How to add FilenameMappingManager to app.py

This shows the minimal changes needed to integrate the filename mapping system
"""

# ============================================================================
# 1. ADD IMPORT AT TOP OF app.py
# ============================================================================

from filename_mapping_manager import FilenameMappingManager

# ============================================================================
# 2. INITIALIZE MANAGER (add after other global variables)
# ============================================================================

# Initialize filename mapping manager
_filename_manager = None

def get_filename_manager():
    """Get or create filename mapping manager"""
    global _filename_manager
    if _filename_manager is None:
        _filename_manager = FilenameMappingManager()
    return _filename_manager

# ============================================================================
# 3. UPDATE _persist_intelligence FUNCTION
# ============================================================================

def _persist_intelligence(intelligence: Dict[str, Any], redacted_filename: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
    """Save intelligence locally and, when available, to Supabase."""
    intelligence_file = _save_intelligence_json(redacted_filename, intelligence)
    persistence = {
        'intelligence_file': intelligence_file,
        'stored_in_supabase': False,
        'stored_embedding_in_supabase': False,
        'supabase_error': None,
        'mapping_stored_in_supabase': False,  # NEW
        'mapping_stored_locally': False       # NEW
    }

    if not SUPABASE_AVAILABLE or 'error' in intelligence:
        return persistence

    storage = get_supabase_storage()
    if not storage:
        return persistence

    try:
        storage.store_intelligence(intelligence)
        anon_id = intelligence.get('anonymized_id')
        if anon_id:
            # EXISTING: Store filename mapping in Supabase
            storage.store_filename_mapping(
                anonymized_id=anon_id,
                original_filename=original_filename or redacted_filename,
                anonymized_filename=redacted_filename
            )
            
            # NEW: Also store in local mapping manager
            filename_manager = get_filename_manager()
            mapping_result = filename_manager.store_mapping(
                anonymized_id=anon_id,
                original_filename=original_filename or redacted_filename,
                anonymized_filename=redacted_filename,
                supabase_storage=storage
            )
            persistence['mapping_stored_in_supabase'] = mapping_result['stored_in_supabase']
            persistence['mapping_stored_locally'] = mapping_result['stored_locally']

            embedding = intelligence.get('embedding')
            if embedding:
                try:
                    storage.store_embedding(
                        anonymized_id=anon_id,
                        embedding=embedding,
                        embedding_model=intelligence.get('embedding_provider')
                    )
                    persistence['stored_embedding_in_supabase'] = True
                except Exception as embedding_error:
                    logger.warning(f"Could not store embedding for {anon_id}: {embedding_error}")

        persistence['stored_in_supabase'] = True
    except Exception as e:
        logger.warning(f"Could not store intelligence in Supabase: {e}")
        persistence['supabase_error'] = str(e)

    return persistence

# ============================================================================
# 4. ADD NEW API ENDPOINT FOR FILENAME LOOKUP (optional)
# ============================================================================

@app.route('/api/filename-lookup', methods=['POST'])
def filename_lookup():
    """
    Lookup filename mapping (admin/backend only)
    
    Request body:
    {
        "anonymized_id": "CAND_882"  // OR
        "original_filename": "John_Doe_Resume.pdf"
    }
    """
    try:
        data = request.get_json()
        filename_manager = get_filename_manager()
        storage = get_supabase_storage()
        
        if 'anonymized_id' in data:
            mapping = filename_manager.get_mapping(data['anonymized_id'], storage)
            if mapping:
                return jsonify({
                    'success': True,
                    'mapping': mapping
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Mapping not found'
                }), 404
        
        elif 'original_filename' in data:
            anon_id = filename_manager.reverse_lookup_by_original(
                data['original_filename'],
                storage
            )
            if anon_id:
                mapping = filename_manager.get_mapping(anon_id, storage)
                return jsonify({
                    'success': True,
                    'anonymized_id': anon_id,
                    'mapping': mapping
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Mapping not found'
                }), 404
        
        else:
            return jsonify({
                'success': False,
                'error': 'Must provide anonymized_id or original_filename'
            }), 400
    
    except Exception as e:
        logger.error(f"Filename lookup error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# 5. ADD SYNC ENDPOINT (optional - for admin recovery)
# ============================================================================

@app.route('/api/sync-filename-mappings', methods=['POST'])
def sync_filename_mappings():
    """
    Sync filename mappings from intelligence files
    Useful for recovery or migration
    """
    try:
        filename_manager = get_filename_manager()
        result = filename_manager.sync_from_intelligence_files(
            intelligence_folder=app.config['INTELLIGENCE_FOLDER']
        )
        
        return jsonify({
            'success': True,
            'stats': result
        })
    
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# USAGE EXAMPLES IN YOUR CODE
# ============================================================================

def example_usage():
    """Examples of how to use the filename manager in your code"""
    
    filename_manager = get_filename_manager()
    storage = get_supabase_storage()
    
    # Example 1: Get original filename from anonymized ID
    original = filename_manager.get_original_filename("CAND_882", storage)
    print(f"Original: {original}")
    
    # Example 2: Find anonymized ID from original filename
    anon_id = filename_manager.reverse_lookup_by_original("John_Doe_Resume.pdf", storage)
    print(f"Anonymized ID: {anon_id}")
    
    # Example 3: Get full mapping
    mapping = filename_manager.get_mapping("CAND_882", storage)
    print(f"Mapping: {mapping}")
    
    # Example 4: Get all mappings (for admin dashboard)
    all_mappings = filename_manager.get_all_mappings(storage)
    print(f"Total mappings: {len(all_mappings)}")
    
    # Example 5: Export for backup
    filename_manager.export_mappings_csv("backup.csv", storage)

# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================

def test_integration():
    """Test the filename mapping integration"""
    
    print("Testing filename mapping integration...")
    
    # Test 1: Store mapping
    filename_manager = get_filename_manager()
    result = filename_manager.store_mapping(
        anonymized_id="TEST_001",
        original_filename="test_resume.pdf",
        anonymized_filename="REDACTED_test.txt",
        supabase_storage=get_supabase_storage()
    )
    print(f"✓ Store mapping: {result}")
    
    # Test 2: Retrieve mapping
    mapping = filename_manager.get_mapping("TEST_001", get_supabase_storage())
    print(f"✓ Retrieve mapping: {mapping}")
    
    # Test 3: Reverse lookup
    anon_id = filename_manager.reverse_lookup_by_original(
        "test_resume.pdf",
        get_supabase_storage()
    )
    print(f"✓ Reverse lookup: {anon_id}")
    
    # Test 4: Sync from intelligence files
    stats = filename_manager.sync_from_intelligence_files()
    print(f"✓ Sync stats: {stats}")
    
    print("\n✅ All tests passed!")

if __name__ == '__main__':
    # Run tests
    test_integration()
