"""
Filename Mapping Manager
Manages the mapping between original filenames and anonymized IDs
with multi-tier storage (Supabase + Local JSON fallback)
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class FilenameMappingManager:
    """
    Manages filename mappings with automatic fallback:
    1. Primary: Supabase database (cv_filename_mapping table)
    2. Fallback: Local JSON file (filename_mappings.json)
    3. Embedded: Each intelligence JSON contains the mapping
    """
    
    def __init__(self, local_mapping_file: str = "filename_mappings.json"):
        """
        Initialize the mapping manager
        
        Args:
            local_mapping_file: Path to local JSON mapping file
        """
        self.local_mapping_file = Path(local_mapping_file)
        self._ensure_local_file_exists()
    
    def _ensure_local_file_exists(self):
        """Create local mapping file if it doesn't exist"""
        if not self.local_mapping_file.exists():
            self._save_local_mappings({})
            logger.info(f"Created local mapping file: {self.local_mapping_file}")
    
    def _load_local_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load mappings from local JSON file"""
        try:
            with open(self.local_mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading local mappings: {e}")
            return {}
    
    def _save_local_mappings(self, mappings: Dict[str, Dict[str, str]]):
        """Save mappings to local JSON file"""
        try:
            with open(self.local_mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving local mappings: {e}")
    
    def store_mapping(
        self,
        anonymized_id: str,
        original_filename: str,
        anonymized_filename: str,
        supabase_storage=None
    ) -> Dict[str, bool]:
        """
        Store filename mapping in both Supabase and local JSON
        
        Args:
            anonymized_id: Anonymized candidate ID (e.g., "CAND_882")
            original_filename: Original uploaded filename
            anonymized_filename: Redacted filename
            supabase_storage: Optional SupabaseStorage instance
        
        Returns:
            Dict with storage status for each tier
        """
        result = {
            'stored_in_supabase': False,
            'stored_locally': False,
            'supabase_error': None
        }
        
        # 1. Try Supabase first (primary storage)
        if supabase_storage:
            try:
                supabase_storage.store_filename_mapping(
                    anonymized_id=anonymized_id,
                    original_filename=original_filename,
                    anonymized_filename=anonymized_filename
                )
                result['stored_in_supabase'] = True
                logger.info(f"✓ Stored mapping in Supabase: {anonymized_id}")
            except Exception as e:
                logger.warning(f"Could not store mapping in Supabase: {e}")
                result['supabase_error'] = str(e)
        
        # 2. Always store locally (fallback storage)
        try:
            mappings = self._load_local_mappings()
            mappings[anonymized_id] = {
                'original_filename': original_filename,
                'anonymized_filename': anonymized_filename,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self._save_local_mappings(mappings)
            result['stored_locally'] = True
            logger.info(f"✓ Stored mapping locally: {anonymized_id}")
        except Exception as e:
            logger.error(f"Failed to store mapping locally: {e}")
        
        return result
    
    def get_mapping(
        self,
        anonymized_id: str,
        supabase_storage=None
    ) -> Optional[Dict[str, str]]:
        """
        Retrieve filename mapping (tries Supabase first, then local)
        
        Args:
            anonymized_id: Anonymized candidate ID
            supabase_storage: Optional SupabaseStorage instance
        
        Returns:
            Dict with original_filename and anonymized_filename, or None
        """
        # 1. Try Supabase first
        if supabase_storage:
            try:
                original = supabase_storage.get_original_filename(anonymized_id)
                if original:
                    # Get full mapping from Supabase
                    response = supabase_storage.client.table("cv_filename_mapping").select(
                        "*"
                    ).eq("anonymized_id", anonymized_id).execute()
                    
                    if response.data:
                        return response.data[0]
            except Exception as e:
                logger.warning(f"Could not retrieve from Supabase: {e}")
        
        # 2. Fallback to local storage
        mappings = self._load_local_mappings()
        return mappings.get(anonymized_id)
    
    def get_original_filename(
        self,
        anonymized_id: str,
        supabase_storage=None
    ) -> Optional[str]:
        """
        Get original filename from anonymized ID
        
        Args:
            anonymized_id: Anonymized candidate ID
            supabase_storage: Optional SupabaseStorage instance
        
        Returns:
            Original filename or None
        """
        mapping = self.get_mapping(anonymized_id, supabase_storage)
        return mapping.get('original_filename') if mapping else None
    
    def get_anonymized_filename(
        self,
        anonymized_id: str,
        supabase_storage=None
    ) -> Optional[str]:
        """
        Get anonymized filename from anonymized ID
        
        Args:
            anonymized_id: Anonymized candidate ID
            supabase_storage: Optional SupabaseStorage instance
        
        Returns:
            Anonymized filename or None
        """
        mapping = self.get_mapping(anonymized_id, supabase_storage)
        return mapping.get('anonymized_filename') if mapping else None
    
    def reverse_lookup_by_original(
        self,
        original_filename: str,
        supabase_storage=None
    ) -> Optional[str]:
        """
        Find anonymized ID from original filename
        
        Args:
            original_filename: Original uploaded filename
            supabase_storage: Optional SupabaseStorage instance
        
        Returns:
            Anonymized ID or None
        """
        # 1. Try Supabase first
        if supabase_storage:
            try:
                response = supabase_storage.client.table("cv_filename_mapping").select(
                    "anonymized_id"
                ).eq("original_filename", original_filename).execute()
                
                if response.data:
                    return response.data[0]['anonymized_id']
            except Exception as e:
                logger.warning(f"Could not search Supabase: {e}")
        
        # 2. Fallback to local storage
        mappings = self._load_local_mappings()
        for anon_id, mapping in mappings.items():
            if mapping.get('original_filename') == original_filename:
                return anon_id
        
        return None
    
    def get_all_mappings(
        self,
        supabase_storage=None
    ) -> List[Dict[str, str]]:
        """
        Get all filename mappings
        
        Args:
            supabase_storage: Optional SupabaseStorage instance
        
        Returns:
            List of mapping dictionaries
        """
        # 1. Try Supabase first
        if supabase_storage:
            try:
                response = supabase_storage.client.table("cv_filename_mapping").select(
                    "*"
                ).execute()
                
                if response.data:
                    return response.data
            except Exception as e:
                logger.warning(f"Could not retrieve all mappings from Supabase: {e}")
        
        # 2. Fallback to local storage
        mappings = self._load_local_mappings()
        return [
            {
                'anonymized_id': anon_id,
                **mapping
            }
            for anon_id, mapping in mappings.items()
        ]
    
    def sync_from_intelligence_files(
        self,
        intelligence_folder: str = "llm_analysis"
    ) -> Dict[str, int]:
        """
        Rebuild local mappings from intelligence JSON files
        Useful for recovery or migration
        
        Args:
            intelligence_folder: Path to intelligence files
        
        Returns:
            Dict with sync statistics
        """
        intelligence_dir = Path(intelligence_folder)
        mappings = self._load_local_mappings()
        
        synced = 0
        skipped = 0
        errors = 0
        
        for json_file in intelligence_dir.glob('*_intelligence.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                anonymized_id = data.get('anonymized_id')
                original_filename = data.get('original_filename')
                redacted_filename = data.get('redacted_filename')
                
                if anonymized_id and original_filename:
                    if anonymized_id not in mappings:
                        mappings[anonymized_id] = {
                            'original_filename': original_filename,
                            'anonymized_filename': redacted_filename or original_filename,
                            'created_at': data.get('analysis_date', datetime.now().isoformat()),
                            'last_updated': datetime.now().isoformat(),
                            'synced_from': str(json_file.name)
                        }
                        synced += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"Error syncing {json_file.name}: {e}")
                errors += 1
        
        self._save_local_mappings(mappings)
        
        return {
            'synced': synced,
            'skipped': skipped,
            'errors': errors,
            'total_mappings': len(mappings)
        }
    
    def export_mappings_csv(
        self,
        output_file: str = "filename_mappings.csv",
        supabase_storage=None
    ):
        """
        Export all mappings to CSV for backup/audit
        
        Args:
            output_file: Output CSV filename
            supabase_storage: Optional SupabaseStorage instance
        """
        import csv
        
        mappings = self.get_all_mappings(supabase_storage)
        
        if not mappings:
            logger.warning("No mappings to export")
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['anonymized_id', 'original_filename', 'anonymized_filename', 'created_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            
            writer.writeheader()
            for mapping in mappings:
                writer.writerow(mapping)
        
        logger.info(f"✓ Exported {len(mappings)} mappings to {output_file}")
