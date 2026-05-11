"""
Flask Web UI for CV Redaction Pipeline with Intelligence Extraction
Allows users to upload CVs, redact PII, extract intelligence, and search candidates
Supports both Supabase and local JSON-based storage with automatic fallback
"""
import os
import sys
import json
import glob
import hashlib
import re
import time
import threading
import queue
import uuid
import io
import zipfile
import mimetypes
from typing import Any, Dict, List, Optional
from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Override system env vars with .env values
except ImportError:
    pass  # dotenv not installed, rely on system env vars

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our pipeline
from universal_pipeline_engine import PipelineOrchestrator
from cv_intelligence_extractor import CVIntelligenceExtractor
from filename_mapping_manager import FilenameMappingManager

# Import Supabase storage (optional)
try:
    from supabase_storage import SupabaseStorage
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase not available. Install with: pip install supabase")


# Configure Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def _resolve_runtime_data_root() -> Path:
    """Return a persistent writable root for runtime data.

    In frozen PyInstaller mode, avoid ephemeral _MEI temp paths and store data
    next to the executable so downloads remain available during app runtime.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(os.path.dirname(os.path.abspath(__file__)))


_RUNTIME_DATA_ROOT = _resolve_runtime_data_root()
app.config['UPLOAD_FOLDER'] = str(_RUNTIME_DATA_ROOT / 'uploads')
app.config['OUTPUT_FOLDER'] = str(_RUNTIME_DATA_ROOT / 'redacted_output')
app.config['INTELLIGENCE_FOLDER'] = str(_RUNTIME_DATA_ROOT / 'llm_analysis')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['ASSET_VERSION'] = os.getenv('ASSET_VERSION', datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))
app.secret_key = 'cv-redaction-secret-key-2024'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)
Path(app.config['INTELLIGENCE_FOLDER']).mkdir(exist_ok=True)

# Initialize intelligence extractor (lazy load)
_intelligence_extractor = None
_supabase_storage = None
_supabase_reachable = None  # Track if Supabase is actually reachable
_quick_search_cache_lock = threading.Lock()
_quick_search_candidate_cache = {
    'updated_at': 0.0,
    'candidates': []
}
_quick_search_cache_refreshing = False
_QUICK_SEARCH_CACHE_TTL_SECONDS = int(os.getenv('QUICK_SEARCH_CACHE_TTL_SECONDS', '45'))
_lock_registry_guard = threading.Lock()
_redaction_lock_registry = {}
_intelligence_lock_registry = {}
_upload_jobs_lock = threading.Lock()
_upload_jobs: Dict[str, Dict[str, Any]] = {}
_upload_job_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
_upload_workers_started = False
_UPLOAD_JOB_TTL_SECONDS = int(os.getenv('UPLOAD_JOB_TTL_SECONDS', '3600'))
_UPLOAD_WORKER_COUNT = max(1, int(os.getenv('UPLOAD_WORKER_COUNT', '2')))  # Reduced from 4 to 2
_UPLOAD_ASYNC_DEFAULT = os.getenv('UPLOAD_ASYNC_DEFAULT', 'true').strip().lower() not in {'0', 'false', 'no'}
_LLM_MAX_CONCURRENT = max(1, int(os.getenv('LLM_MAX_CONCURRENT_REQUESTS', '1')))  # Reduced from 2 to 1
_LLM_MIN_INTERVAL_SECONDS = max(0.0, float(os.getenv('LLM_MIN_INTERVAL_SECONDS', '0.35')))
_llm_request_semaphore = threading.BoundedSemaphore(_LLM_MAX_CONCURRENT)
_llm_rate_lock = threading.Lock()
_last_llm_request_at = 0.0
_DEFAULT_PROFILE_JD = (
    "General candidate profiling for recruiter search: extract skills, years of experience, "
    "seniority level, domain expertise, strengths, and evidence-based summary for ranking."
)

_filename_mapping_manager = FilenameMappingManager(local_mapping_file=str(_RUNTIME_DATA_ROOT / 'filename_mappings.json'))


def _get_filename_mapping(anonymized_id: str, storage) -> Optional[Dict[str, Any]]:
    """Resolve filename mapping for a candidate from Supabase or local fallback."""
    try:
        return _filename_mapping_manager.get_mapping(anonymized_id=anonymized_id, supabase_storage=storage)
    except Exception as e:
        logger.warning(f"Failed to resolve filename mapping for {anonymized_id}: {e}")
        return None


def _find_latest_upload_for_original_filename(original_filename: str) -> Optional[Path]:
    """Find the most recently uploaded file matching an original filename."""
    if not original_filename:
        return None

    raw_basename = Path(original_filename).name
    safe_original = secure_filename(raw_basename)
    if not safe_original:
        return None

    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    candidates = list(upload_dir.glob(f"*_{safe_original}"))
    if not candidates:
        direct = upload_dir / safe_original
        if direct.exists():
            return direct
        return None

    # Pick the newest by mtime
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _find_original_cv_anywhere(original_filename: str) -> Optional[Path]:
    """Best-effort lookup for original CV across known runtime folders."""
    upload_hit = _find_latest_upload_for_original_filename(original_filename)
    if upload_hit and upload_hit.exists():
        return upload_hit

    raw_basename = Path(original_filename).name
    safe_original = secure_filename(raw_basename)
    if not safe_original:
        return None

    # Common local test-data locations.
    search_roots = [
        _RUNTIME_DATA_ROOT / 'archive' / 'samples',
        _RUNTIME_DATA_ROOT / 'samples',
    ]

    best: Optional[Path] = None
    best_mtime = -1.0
    for root in search_roots:
        if not root.exists():
            continue

        try:
            for path in root.rglob('*'):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in {'.pdf', '.doc', '.docx'}:
                    continue
                if path.name == raw_basename or secure_filename(path.name) == safe_original:
                    mtime = path.stat().st_mtime
                    if mtime > best_mtime:
                        best = path
                        best_mtime = mtime
        except Exception:
            continue

    return best


def _supabase_get_original_filenames(storage, anonymized_ids: List[str]) -> Dict[str, Optional[str]]:
    """Best-effort batch lookup of original filenames from Supabase cv_intelligence."""
    if not storage or not anonymized_ids:
        return {}

    ids = [str(x).strip() for x in anonymized_ids if str(x).strip()]
    if not ids:
        return {}

    def _query():
        try:
            resp = (
                storage.client.table('cv_intelligence')
                .select('anonymized_id, original_filename')
                .in_('anonymized_id', ids)
                .execute()
            )
        except Exception as e:
            # Some deployments may not have original_filename column.
            msg = str(e)
            if "Could not find the 'original_filename' column" in msg or 'original_filename' in msg:
                logger.warning("Supabase cv_intelligence.original_filename not available; falling back to local-only resolution")
                return {}
            raise

        rows = resp.data or []
        result: Dict[str, Optional[str]] = {}
        for row in rows:
            anon = row.get('anonymized_id')
            if not anon:
                continue
            result[str(anon)] = row.get('original_filename')
        return result

    # Use timeout wrapper for network safety; query itself handles schema mismatches.
    return try_supabase_operation(_query, fallback_result={}, timeout_seconds=10) or {}


def _redact_cv_text_only(cv_path: Path) -> str:
    """Run redaction pipeline only (no LLM) and return redacted text."""
    orchestrator = PipelineOrchestrator(config_dir='config')
    redacted_text, _profile = orchestrator.process_cv(str(cv_path))
    return redacted_text


def _parse_archive_source_rel_path(best_knowledge_summary: Any) -> Optional[str]:
    """Extract archive relative path from strings like 'Source: foo/bar.pdf'."""
    if not best_knowledge_summary:
        return None
    text = str(best_knowledge_summary).strip()
    if not text:
        return None
    match = re.search(r"\bSource:\s*([^\r\n]+)", text)
    if not match:
        return None
    rel_path = match.group(1).strip().strip('"\'')
    if not rel_path:
        return None
    # Normalize slashes.
    rel_path = rel_path.replace('\\', '/')
    # Prevent traversal.
    rel_path = rel_path.lstrip('/').replace('..', '')
    return rel_path or None


def _safe_join_under(root: Path, rel_path: str) -> Optional[Path]:
    """Resolve rel_path under root; return None if it escapes root."""
    if not rel_path:
        return None
    candidate = (root / rel_path).resolve()
    try:
        root_resolved = root.resolve()
        if str(candidate).startswith(str(root_resolved)):
            return candidate
    except Exception:
        return None
    return None


def _supabase_get_candidate_fields(storage, anonymized_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Batch fetch a few fields needed for downloads (cleaned_text, best_knowledge_summary, etc.)."""
    if not storage or not anonymized_ids:
        return {}
    ids = [str(x).strip() for x in anonymized_ids if str(x).strip()]
    if not ids:
        return {}

    def _query():
        resp = (
            storage.client.table('cv_intelligence')
            .select('anonymized_id, cleaned_text, best_knowledge_summary')
            .in_('anonymized_id', ids)
            .execute()
        )
        rows = resp.data or []
        result: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            anon = row.get('anonymized_id')
            if not anon:
                continue
            result[str(anon)] = row
        return result

    return try_supabase_operation(_query, fallback_result={}, timeout_seconds=12) or {}


def _fallback_filenames_from_local_intelligence(anonymized_id: str) -> Dict[str, Optional[str]]:
    """Best-effort local fallback to recover filenames from intelligence JSON."""
    result = {
        'original_filename': None,
        'redacted_filename': None
    }

    if not anonymized_id:
        return result

    intelligence_dir = Path(app.config['INTELLIGENCE_FOLDER'])
    try:
        for json_file in intelligence_dir.glob('*_intelligence.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('anonymized_id') != anonymized_id:
                    continue
                result['original_filename'] = data.get('original_filename')
                result['redacted_filename'] = data.get('redacted_filename')
                return result
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Local intelligence fallback scan failed: {e}")

    return result


def _get_named_lock(lock_registry: Dict[str, threading.Lock], key: str) -> threading.Lock:
    """Return a stable in-process lock for a key (single-flight helper)."""
    with _lock_registry_guard:
        lock = lock_registry.get(key)
        if lock is None:
            lock = threading.Lock()
            lock_registry[key] = lock
        return lock


def _sha256_for_file(file_path: Path) -> str:
    """Compute a deterministic hash for a source CV file."""
    digest = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_bool(value: Any, default: bool = False) -> bool:
    """Parse boolean-like values from form/query payloads."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {'1', 'true', 'yes', 'on'}:
        return True
    if text in {'0', 'false', 'no', 'off'}:
        return False
    return default


def _run_llm_with_rate_limit(extractor, redacted_text: str, job_description: Optional[str], source_name: str):
    """Protect provider APIs from request bursts with concurrency + pacing limits."""
    global _last_llm_request_at

    with _llm_request_semaphore:
        with _llm_rate_lock:
            now = time.time()
            wait_time = _LLM_MIN_INTERVAL_SECONDS - (now - _last_llm_request_at)
            if wait_time > 0:
                time.sleep(wait_time)
            _last_llm_request_at = time.time()

        return extractor.extract_intelligence(redacted_text, job_description, source_name)


@app.after_request
def disable_static_cache(response):
    """Prevent stale frontend assets from breaking updated client-side behavior."""
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


@app.context_processor
def inject_asset_version():
    """Inject static asset version for deterministic cache busting."""
    return {'asset_version': app.config.get('ASSET_VERSION', '1')}

def get_intelligence_extractor():
    """Get or create default intelligence extractor."""
    return get_runtime_intelligence_extractor()


def get_runtime_intelligence_extractor(
    api_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    llm_model: Optional[str] = None
):
    """Return default cached extractor, or a request-scoped one for per-user keys."""
    global _intelligence_extractor

    runtime_override = bool(api_provider or api_key or llm_model)
    if runtime_override:
        provider = (api_provider or os.getenv('LLM_PROVIDER', 'groq')).strip().lower()
        model = llm_model or os.getenv('LLM_MODEL', None)
        return CVIntelligenceExtractor(api_provider=provider, api_key=api_key, model=model)

    if _intelligence_extractor is None:
        provider = os.getenv('LLM_PROVIDER', 'groq')
        model = os.getenv('LLM_MODEL', None)
        _intelligence_extractor = CVIntelligenceExtractor(api_provider=provider, model=model)
    return _intelligence_extractor


def _extract_runtime_llm_config(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Optional[str]]:
    """Read optional per-user LLM settings from request payload or headers."""
    payload = payload or {}
    llm_config = payload.get('llm_config') or {}
    if not isinstance(llm_config, dict):
        llm_config = {}

    provider = (
        llm_config.get('provider')
        or payload.get('llm_provider')
        or request.headers.get('X-LLM-Provider')
        or None
    )
    api_key = (
        llm_config.get('api_key')
        or payload.get('llm_api_key')
        or request.headers.get('X-LLM-Api-Key')
        or None
    )
    model = (
        llm_config.get('model')
        or payload.get('llm_model')
        or request.headers.get('X-LLM-Model')
        or None
    )

    allowed_providers = {'openai', 'anthropic', 'gemini', 'groq', 'ollama'}
    provider = provider.strip().lower() if isinstance(provider, str) and provider.strip() else None
    if provider and provider not in allowed_providers:
        provider = None

    api_key = api_key.strip() if isinstance(api_key, str) and api_key.strip() else None
    model = model.strip() if isinstance(model, str) and model.strip() else None

    return {
        'provider': provider,
        'api_key': api_key,
        'model': model
    }


def _get_quick_search_cache_snapshot() -> List[Dict[str, Any]]:
    """Return a shallow copy of cached quick-search candidates."""
    with _quick_search_cache_lock:
        return list(_quick_search_candidate_cache.get('candidates') or [])


def _invalidate_quick_search_cache(reason: str = '') -> None:
    """Force next quick-search call to refetch latest candidates from Supabase."""
    with _quick_search_cache_lock:
        _quick_search_candidate_cache['candidates'] = []
        _quick_search_candidate_cache['updated_at'] = 0.0
    if reason:
        logger.info("Quick-search cache invalidated: %s", reason)


def _get_quick_search_candidates(storage, limit: int = 5000) -> Dict[str, Any]:
    """Get candidates for quick-search using Supabase with TTL cache and stale fallback."""
    global _quick_search_cache_refreshing
    now = time.time()
    should_refresh = False

    with _quick_search_cache_lock:
        cached_candidates = list(_quick_search_candidate_cache.get('candidates') or [])
        cache_age = now - float(_quick_search_candidate_cache.get('updated_at') or 0.0)
        if cached_candidates and cache_age <= _QUICK_SEARCH_CACHE_TTL_SECONDS:
            return {
                'candidates': cached_candidates,
                'source': 'supabase_cache',
                'cache_age_seconds': round(cache_age, 3)
            }

        if _quick_search_cache_refreshing:
            if cached_candidates:
                return {
                    'candidates': cached_candidates,
                    'source': 'supabase_cache_stale',
                    'cache_age_seconds': round(cache_age, 3)
                }
            return {
                'candidates': [],
                'source': 'supabase_refresh_in_progress',
                'cache_age_seconds': None
            }

        _quick_search_cache_refreshing = True
        should_refresh = True

    raw_candidates = try_supabase_operation(
        lambda: storage.get_all_candidates(limit=limit),
        fallback_result=None,
        timeout_seconds=10
    )

    if raw_candidates is not None:
        candidate_rows = [
            storage._db_record_to_app_format(record)
            for record in raw_candidates
        ]
        with _quick_search_cache_lock:
            _quick_search_candidate_cache['candidates'] = list(candidate_rows)
            _quick_search_candidate_cache['updated_at'] = time.time()
            _quick_search_cache_refreshing = False
            return {
                'candidates': candidate_rows,
                'source': 'supabase_live',
                'cache_age_seconds': 0.0
            }

    with _quick_search_cache_lock:
        _quick_search_cache_refreshing = False
        cached_candidates = list(_quick_search_candidate_cache.get('candidates') or [])
        cache_age = time.time() - float(_quick_search_candidate_cache.get('updated_at') or 0.0)
        if cached_candidates:
            return {
                'candidates': cached_candidates,
                'source': 'supabase_cache_stale',
                'cache_age_seconds': round(cache_age, 3)
            }

        return {
            'candidates': [],
            'source': 'supabase_unavailable',
            'cache_age_seconds': None
        }

def get_supabase_storage():
    """Get or create Supabase storage with timeout handling"""
    global _supabase_storage, _supabase_reachable
    if _supabase_reachable is False:
        return None
    if _supabase_storage is None and SUPABASE_AVAILABLE:
        try:
            _supabase_storage = SupabaseStorage()
            # Don't mark as reachable until first successful query
        except Exception as e:
            logger.warning(f"Supabase not reachable: {e}")
            _supabase_storage = None
            _supabase_reachable = False
    return _supabase_storage

def try_supabase_operation(operation, fallback_result=None, timeout_seconds=5):
    """
    Try a Supabase operation with a timeout. Falls back gracefully on failure.
    
    Args:
        operation: callable to execute
        fallback_result: value to return on failure
        timeout_seconds: max seconds to wait
    
    Returns:
        Result of operation, or fallback_result on failure
    """
    import threading
    result_holder = [fallback_result]
    error_holder = [None]
    
    def run_operation():
        try:
            result_holder[0] = operation()
        except Exception as e:
            error_holder[0] = e
    
    thread = threading.Thread(target=run_operation, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        global _supabase_reachable
        _supabase_reachable = False
        logger.warning(f"Supabase operation timed out after {timeout_seconds}s, switching to local mode")
        return fallback_result
    
    if error_holder[0]:
        _supabase_reachable = False
        logger.warning(f"Supabase operation failed: {error_holder[0]}, switching to local mode")
        return fallback_result
    
    # Mark as reachable on success
    _supabase_reachable = True
    return result_holder[0]

def is_supabase_configured():
    """Check if Supabase credentials are configured (without connecting)"""
    return SUPABASE_AVAILABLE and bool(os.getenv('SUPABASE_URL')) and bool(os.getenv('SUPABASE_KEY'))


def _has_real_secret(env_var_name: str) -> bool:
    """Check whether an env var looks like a real configured secret instead of a placeholder."""
    value = os.getenv(env_var_name, '')
    if not value:
        return False
    lowered = value.lower()
    return 'your-' not in lowered and 'placeholder' not in lowered and 'change-this' not in lowered


def probe_llm_provider() -> Dict[str, Any]:
    """Run a small live probe against the configured LLM provider when supported."""
    provider = os.getenv('LLM_PROVIDER', 'groq').lower()
    model = os.getenv('LLM_MODEL', '')

    status = {
        'provider': provider,
        'model': model,
        'configured': True,
        'reachable': False,
        'message': ''
    }

    if provider == 'groq':
        status['configured'] = _has_real_secret('GROQ_API_KEY')

    if not status['configured']:
        status['message'] = 'not configured'
        return status

    try:
        if provider == 'groq':
            from groq import Groq

            client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            response = client.chat.completions.create(
                model=model or 'llama-3.3-70b-versatile',
                messages=[{'role': 'user', 'content': 'Reply with exactly OK'}],
                temperature=0,
                max_tokens=5
            )
            content = response.choices[0].message.content if response and response.choices else ''
            status['reachable'] = str(content).strip().upper().startswith('OK')
            status['message'] = 'live Groq probe succeeded'
        elif provider == 'ollama':
            import ollama

            response = ollama.chat(
                model=model or 'qwen2.5:7b',
                messages=[{'role': 'user', 'content': 'Reply with exactly OK'}],
                options={'temperature': 0, 'num_predict': 5}
            )
            content = response.get('message', {}).get('content', '')
            status['reachable'] = str(content).strip().upper().startswith('OK')
            status['message'] = 'live Ollama probe succeeded'
        else:
            status['message'] = f'live probe not implemented for provider: {provider}'
    except Exception as e:
        status['message'] = str(e)

    return status


def probe_embedding_runtime() -> Dict[str, Any]:
    """Verify embeddings can be generated with the configured provider."""
    provider = os.getenv('EMBEDDING_PROVIDER', 'local')
    status = {
        'provider': provider,
        'configured': True,
        'reachable': False,
        'dimensions': None,
        'message': ''
    }

    if provider == 'openai':
        status['configured'] = _has_real_secret('OPENAI_API_KEY')

    try:
        from vector_search import get_vector_search_engine
        engine = get_vector_search_engine(embedding_provider=provider)
        vector = engine.generate_embedding('python backend developer')
        status['reachable'] = bool(vector)
        status['dimensions'] = len(vector) if vector else 0
        status['message'] = 'embedding probe succeeded'
    except Exception as e:
        status['message'] = str(e)

    return status


def probe_supabase_runtime() -> Dict[str, Any]:
    """Run a real Supabase probe using the configured database credentials."""
    status = {
        'configured': is_supabase_configured(),
        'reachable': False,
        'message': 'not configured'
    }

    if not status['configured']:
        return status

    try:
        storage = get_supabase_storage()
        if not storage:
            status['message'] = 'storage client unavailable'
            return status

        response = storage.client.table('cv_intelligence').select('anonymized_id').limit(1).execute()
        status['reachable'] = isinstance(response.data, list)
        status['message'] = f'live Supabase probe succeeded ({len(response.data)} rows sample)'
    except Exception as e:
        status['message'] = str(e)

    return status


# ============================================================================
# LOCAL JSON STORAGE FALLBACK
# ============================================================================

def load_local_intelligence_files():
    """Load all intelligence JSON files from local disk as fallback data source"""
    intelligence_dir = Path(app.config['INTELLIGENCE_FOLDER'])
    candidates = []
    
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Skip files with errors
            if 'error' in data and not data.get('verdict'):
                continue
            
            # Ensure minimum required fields
            if not data.get('anonymized_id'):
                continue
            
            # Normalize fields for display
            candidate = {
                'anonymized_id': data.get('anonymized_id', 'UNKNOWN'),
                'verdict': data.get('verdict'),  # Can be None for extraction-only
                'has_jd_matching': data.get('has_jd_matching', data.get('match_score') is not None),
                'confidence_score': data.get('confidence_score', 0),
                'match_score': data.get('match_score'),  # Can be None
                'years_experience': data.get('years_experience', 0),
                'seniority_level': data.get('seniority_level', ''),
                'core_technical_skills': data.get('core_technical_skills', []),
                'secondary_technical_skills': data.get('secondary_technical_skills', []),
                'frameworks_tools': data.get('frameworks_tools', []),
                'primary_domain': data.get('primary_domain', ''),
                'secondary_domains': data.get('secondary_domains', []),
                'leadership_indicators': data.get('leadership_indicators', []),
                'cleaned_narrative': data.get('cleaned_narrative', ''),
                'verdict_reason': data.get('verdict_reason', ''),
                'requires_human_review': data.get('requires_human_review', False),
                'recruiter_override': data.get('recruiter_override'),
                'original_filename': data.get('original_filename', ''),
                'analysis_date': data.get('analysis_date', ''),
                'matched_requirements': data.get('matched_requirements', []),
                'missing_requirements': data.get('missing_requirements', []),
                'key_strengths': data.get('key_strengths', []),
                'potential_concerns': data.get('potential_concerns', []),
                '_source': 'local_json',
                '_filename': str(json_file.name)
            }
            candidates.append(candidate)
        except Exception as e:
            logger.debug(f"Skipping {json_file.name}: {e}")
    
    return candidates

def get_local_statistics():
    """Calculate statistics from local JSON intelligence files"""
    candidates = [c for c in load_local_intelligence_files() if _candidate_has_searchable_signal(c)]
    total = len(candidates)
    
    if total == 0:
        return {
            'total_candidates': 0,
            'shortlisted': 0,
            'backup': 0,
            'review_needed': 0,
            'extracted_only': 0,
            'requires_human_review': 0,
            'recruiter_reviewed': 0,
            'average_match_score': 'N/A',
            'average_confidence_score': 0,
            'data_source': 'local_json'
        }
    
    shortlisted = len([c for c in candidates if c.get('verdict') == 'SHORTLIST'])
    backup = len([c for c in candidates if c.get('verdict') == 'BACKUP'])
    review = 0
    extracted_only = len([c for c in candidates if c.get('verdict') is None or c.get('has_jd_matching') == False])
    human_review = 0
    reviewed = len([c for c in candidates if c.get('recruiter_override')])
    
    # Calculate average match score only for CVs with JD matching
    cvs_with_jd = [c for c in candidates if c.get('match_score') is not None]
    avg_match = sum(c.get('match_score', 0) for c in cvs_with_jd) / len(cvs_with_jd) if cvs_with_jd else 'N/A'
    avg_conf = sum(c.get('confidence_score', 0) for c in candidates) / total
    
    return {
        'total_candidates': total,
        'shortlisted': shortlisted,
        'backup': backup,
        'review_needed': review,
        'extracted_only': extracted_only,
        'requires_human_review': human_review,
        'recruiter_reviewed': reviewed,
        'average_match_score': round(avg_match, 2) if isinstance(avg_match, (int, float)) else avg_match,
        'average_confidence_score': round(avg_conf, 2),
        'data_source': 'local_json'
    }

def search_local_candidates(filters):
    """Search local JSON candidates with filters"""
    candidates = load_local_intelligence_files()
    return _filter_candidate_records(candidates, filters)


def _filter_candidate_records(candidates: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply candidate search filters to in-memory candidate records."""
    verdict = filters.get('verdict')
    seniority = filters.get('seniority_level')
    min_score = filters.get('min_match_score')
    min_conf = filters.get('min_confidence_score')
    primary_domain = filters.get('primary_domain')
    min_years = filters.get('min_years_experience')
    max_years = filters.get('max_years_experience')
    required_skills = filters.get('required_skills') or []
    domains = filters.get('domains') or []

    def normalize_terms(value) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip().lower()] if value.strip() else []
        terms = []
        for item in value:
            item_str = str(item).strip().lower()
            if item_str:
                terms.append(item_str)
        return terms

    required_skills_norm = normalize_terms(required_skills)
    domains_norm = normalize_terms(domains)
    primary_domain_norm = str(primary_domain or '').strip().lower()

    results = []
    for c in candidates:
        if not _candidate_has_searchable_signal(c):
            continue

        if verdict and c.get('verdict') != verdict:
            continue
        if seniority and c.get('seniority_level') != seniority:
            continue

        if min_score is not None and float(c.get('match_score') or 0) < float(min_score):
            continue
        if min_conf is not None and float(c.get('confidence_score') or 0) < float(min_conf):
            continue

        years_exp = float(c.get('years_experience') or 0)
        if min_years is not None and years_exp < float(min_years):
            continue
        if max_years is not None and years_exp > float(max_years):
            continue

        searchable_skills = [
            str(skill).strip().lower()
            for skill in (
                (c.get('core_technical_skills') or [])
                + (c.get('secondary_technical_skills') or [])
                + (c.get('key_skills') or [])
                + (c.get('frameworks_tools') or [])
            )
            if str(skill).strip()
        ]
        if required_skills_norm:
            if not all(any(req in skill for skill in searchable_skills) for req in required_skills_norm):
                continue

        domain_parts = [
            c.get('primary_domain', ''),
            ' '.join(c.get('secondary_domains') or []),
            ' '.join(c.get('domain_expertise') or []),
            c.get('cleaned_narrative', ''),
            c.get('overall_summary', '')
        ]
        searchable_domain_text = ' '.join(str(part).lower() for part in domain_parts if str(part).strip())

        if primary_domain_norm and primary_domain_norm not in searchable_domain_text:
            continue

        if domains_norm and not any(domain in searchable_domain_text for domain in domains_norm):
            continue

        results.append(c)

    results.sort(
        key=lambda x: (
            float(x.get('match_score') or 0),
            float(x.get('confidence_score') or 0),
            float(x.get('years_experience') or 0)
        ),
        reverse=True
    )
    return results


# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _current_jd_hash(job_description: Optional[str]) -> Optional[str]:
    """Create a stable hash for the active job description."""
    if not job_description:
        return None
    return hashlib.sha256(job_description.encode('utf-8')).hexdigest()[:16]


def _load_cached_intelligence(redacted_filename: str) -> Optional[Dict[str, Any]]:
    """Load a previously saved intelligence file for a redacted CV."""
    intelligence_path = Path(app.config['INTELLIGENCE_FOLDER']) / f"{Path(redacted_filename).stem}_intelligence.json"
    if not intelligence_path.exists():
        return None

    try:
        with open(intelligence_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read cached intelligence for {redacted_filename}: {e}")
        return None


def _is_cached_result_compatible(intelligence: Optional[Dict[str, Any]], job_description: Optional[str]) -> bool:
    """Ensure we only reuse cached results for the same JD mode/hash."""
    if not intelligence or 'error' in intelligence:
        return False

    cached_has_jd = bool(intelligence.get('has_jd_matching'))
    requested_has_jd = bool(job_description)
    if cached_has_jd != requested_has_jd:
        return False

    if not requested_has_jd:
        return True

    return intelligence.get('job_description_hash') == _current_jd_hash(job_description)


def _save_intelligence_json(redacted_filename: str, intelligence: Dict[str, Any]) -> str:
    """Persist intelligence locally so the app always has a disk fallback."""
    intelligence_file = f"{Path(redacted_filename).stem}_intelligence.json"
    intelligence_path = Path(app.config['INTELLIGENCE_FOLDER']) / intelligence_file
    with open(intelligence_path, 'w', encoding='utf-8') as f:
        json.dump(intelligence, f, indent=2, ensure_ascii=False)
    return intelligence_file


def _attach_embedding(intelligence: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a semantic embedding without making processing fail if the model is unavailable."""
    if 'error' in intelligence:
        return {
            'embedding_generated': False,
            'embedding_error': intelligence.get('error')
        }

    existing_embedding = intelligence.get('embedding')
    if existing_embedding:
        return {
            'embedding_generated': True,
            'embedding_dimensions': len(existing_embedding)
        }

    try:
        from vector_search import generate_embedding_for_intelligence

        embedding = generate_embedding_for_intelligence(intelligence)
        if embedding:
            intelligence['embedding'] = embedding
            intelligence['embedding_dimensions'] = len(embedding)
            intelligence['embedding_provider'] = os.getenv('EMBEDDING_PROVIDER', 'local')
            intelligence['embedding_generated_at'] = datetime.now().isoformat()
            return {
                'embedding_generated': True,
                'embedding_dimensions': len(embedding)
            }

        return {
            'embedding_generated': False,
            'embedding_error': 'Empty embedding generated'
        }
    except Exception as e:
        logger.warning(f"Embedding generation unavailable for {intelligence.get('anonymized_id', 'unknown')}: {e}")
        intelligence['embedding_error'] = str(e)
        return {
            'embedding_generated': False,
            'embedding_error': str(e)
        }


def _persist_intelligence(intelligence: Dict[str, Any], redacted_filename: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
    """Save intelligence locally and, when available, to Supabase."""
    intelligence_file = _save_intelligence_json(redacted_filename, intelligence)
    persistence = {
        'intelligence_file': intelligence_file,
        'stored_in_supabase': False,
        'stored_embedding_in_supabase': False,
        'supabase_error': None
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
            storage.store_filename_mapping(
                anonymized_id=anon_id,
                original_filename=original_filename or redacted_filename,
                anonymized_filename=redacted_filename
            )

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
        _invalidate_quick_search_cache(reason=f"new_or_updated_candidate:{intelligence.get('anonymized_id', 'unknown')}")
    except Exception as e:
        logger.warning(f"Could not store intelligence in Supabase: {e}")
        persistence['supabase_error'] = str(e)

    return persistence


def process_redacted_cv_text(
    redacted_text: str,
    redacted_filename: str,
    job_description: Optional[str] = None,
    original_filename: Optional[str] = None,
    force_reprocess: bool = False,
    llm_runtime_config: Optional[Dict[str, Optional[str]]] = None
) -> Dict[str, Any]:
    """Run the LLM, faithfulness, embedding, and persistence stages for an anonymized CV."""
    from cv_intelligence_extractor import is_cv_anonymized

    cache_key = f"{redacted_filename}:{_current_jd_hash(job_description) or 'no_jd'}"
    cache_lock = _get_named_lock(_intelligence_lock_registry, cache_key)

    with cache_lock:
        if not is_cv_anonymized(redacted_text):
            return {
                'success': False,
                'error': 'CV is not anonymized. Please redact PII first.',
                'redacted_filename': redacted_filename
            }

        if not force_reprocess:
            cached = _load_cached_intelligence(redacted_filename)
            if _is_cached_result_compatible(cached, job_description):
                if not cached.get('best_knowledge_summary'):
                    cached['best_knowledge_summary'] = _best_knowledge_summary(cached)
                persistence = _persist_intelligence(cached, redacted_filename, original_filename=original_filename)
                return {
                    'success': True,
                    'cached': True,
                    'redacted_filename': redacted_filename,
                    'intelligence': cached,
                    'intelligence_file': f"{Path(redacted_filename).stem}_intelligence.json",
                    'stored_in_supabase': persistence.get('stored_in_supabase', False),
                    'stored_embedding_in_supabase': persistence.get('stored_embedding_in_supabase', False),
                    'embedding_generated': bool(cached.get('embedding')),
                    'similarity_score': cached.get('similarity_score'),
                    'supabase_error': persistence.get('supabase_error')
                }

        llm_runtime_config = llm_runtime_config or {}
        extractor = get_runtime_intelligence_extractor(
            api_provider=llm_runtime_config.get('provider'),
            api_key=llm_runtime_config.get('api_key'),
            llm_model=llm_runtime_config.get('model')
        )
        intelligence = _run_llm_with_rate_limit(
            extractor=extractor,
            redacted_text=redacted_text,
            job_description=job_description,
            source_name=original_filename or redacted_filename
        )

        if intelligence.get('error') == 'CV_NOT_ANONYMIZED':
            return {
                'success': False,
                'error': intelligence.get('error_message', 'CV is not anonymized.'),
                'redacted_filename': redacted_filename
            }

        intelligence['redacted_filename'] = redacted_filename
        if not intelligence.get('best_knowledge_summary'):
            intelligence['best_knowledge_summary'] = _best_knowledge_summary(intelligence)

        embedding_state = _attach_embedding(intelligence)
        persistence = _persist_intelligence(intelligence, redacted_filename, original_filename=original_filename)

        return {
            'success': 'error' not in intelligence,
            'cached': False,
            'redacted_filename': redacted_filename,
            'intelligence': intelligence,
            'similarity_score': intelligence.get('similarity_score'),
            **embedding_state,
            **persistence
        }


def process_source_cv(
    cv_path: Path,
    job_description: Optional[str] = None,
    force_reprocess: bool = False,
    existing_redacted_path: Optional[Path] = None,
    llm_runtime_config: Optional[Dict[str, Optional[str]]] = None
) -> Dict[str, Any]:
    """Execute the full architecture for an original CV file starting from redaction."""
    original_filename = cv_path.name
    # Upload handler prefixes stored filenames with a timestamp; recover the user-facing
    # source filename so extraction logic receives stable inputs.
    timestamp_prefix_match = re.match(r'^\d{8}_\d{6}_(.+)$', original_filename)
    if timestamp_prefix_match:
        original_filename = timestamp_prefix_match.group(1)

    if existing_redacted_path and existing_redacted_path.exists():
        redacted_path = existing_redacted_path
        redacted_filename = existing_redacted_path.name
        with open(existing_redacted_path, 'r', encoding='utf-8') as f:
            redacted_text = f.read()
    else:
        source_hash = _sha256_for_file(cv_path)[:16]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Use only hash and timestamp - NO original filename for privacy
        redacted_filename = f"REDACTED_{timestamp}_{source_hash}.txt"
        redacted_path = Path(app.config['OUTPUT_FOLDER']) / redacted_filename

        redaction_lock = _get_named_lock(_redaction_lock_registry, source_hash)
        with redaction_lock:
            if redacted_path.exists() and not force_reprocess:
                with open(redacted_path, 'r', encoding='utf-8') as f:
                    redacted_text = f.read()
            else:
                orchestrator = PipelineOrchestrator(config_dir='config')
                redacted_text, profile = orchestrator.process_cv(str(cv_path))
                with open(redacted_path, 'w', encoding='utf-8') as f:
                    f.write(redacted_text)

    if redacted_text.startswith("[ERROR: No text extracted"):
        return {
            'success': False,
            'error': 'No extractable text found in CV',
            'redacted_filename': redacted_filename,
            'preview': redacted_text
        }

    result = process_redacted_cv_text(
        redacted_text=redacted_text,
        redacted_filename=redacted_filename,
        job_description=job_description,
        original_filename=original_filename,
        force_reprocess=force_reprocess,
        llm_runtime_config=llm_runtime_config
    )
    result['preview'] = redacted_text
    return result


def _build_upload_success_payload(pipeline_result: Dict[str, Any], mode: str = 'synchronous') -> Dict[str, Any]:
    """Build a stable API response from a completed pipeline result."""
    if not isinstance(pipeline_result, dict):
        return {
            'success': False,
            'mode': mode,
            'message': 'Invalid pipeline result',
            'error': 'pipeline_result_not_object'
        }

    redacted_filename = pipeline_result.get('redacted_filename')
    if not redacted_filename:
        return {
            'success': False,
            'mode': mode,
            'message': 'Pipeline result missing redacted filename',
            'error': 'missing_redacted_filename'
        }

    response = {
        'success': True,
        'mode': mode,
        'message': 'CV processed successfully',
        'output_filename': redacted_filename,
        'preview': pipeline_result.get('preview', ''),
        'download_url': url_for('download_file', filename=redacted_filename)
    }

    intelligence = pipeline_result.get('intelligence')
    if intelligence:
        response.update({
            'pipeline_executed': 'full',
            'intelligence': intelligence,
            'intelligence_file': pipeline_result.get('intelligence_file'),
            'stored_in_supabase': pipeline_result.get('stored_in_supabase', False),
            'stored_embedding_in_supabase': pipeline_result.get('stored_embedding_in_supabase', False),
            'embedding_generated': pipeline_result.get('embedding_generated', False),
            'similarity_score': pipeline_result.get('similarity_score')
        })
    else:
        response['pipeline_executed'] = 'redaction_only'

    return response


def _cleanup_upload_jobs_locked(now_ts: Optional[float] = None) -> None:
    """Remove completed/failed jobs older than TTL to avoid memory growth."""
    now_ts = now_ts or time.time()
    expired_ids = []
    for job_id, job in _upload_jobs.items():
        status = job.get('status')
        terminal = status in {'completed', 'failed'}
        completed_at = float(job.get('completed_ts') or 0.0)
        if terminal and completed_at and (now_ts - completed_at) > _UPLOAD_JOB_TTL_SECONDS:
            expired_ids.append(job_id)
            logger.info(f"Cleaning up expired job {job_id}: status={status}, age={(now_ts - completed_at):.1f}s")

    for job_id in expired_ids:
        _upload_jobs.pop(job_id, None)


def _create_async_upload_job(
    upload_path: str,
    original_filename: str,
    job_description: Optional[str],
    llm_runtime_config: Optional[Dict[str, Optional[str]]],
    force_reprocess: bool
) -> str:
    """Create and enqueue an async upload job (memory-only for now to reduce memory usage)."""
    job_id = f"job_{uuid.uuid4().hex[:16]}"
    
    # TEMPORARILY DISABLED: Supabase job tracking to reduce memory usage
    # Will re-enable after memory optimization
    # storage = get_supabase_storage()
    # if storage:
    #     try:
    #         result = storage.create_upload_job(...)
    #     except Exception as e:
    #         logger.warning(f"Failed to create job in Supabase: {e}")
    
    # Create in memory
    now_ts = time.time()
    record = {
        'job_id': job_id,
        'status': 'queued',
        'submitted_at': datetime.now().isoformat(),
        'submitted_ts': now_ts,
        'completed_ts': None,
        'upload_path': upload_path,
        'original_filename': original_filename,
        'job_description_provided': bool(job_description),
        'job_description': job_description,
        'llm_runtime_config': llm_runtime_config or {},
        'force_reprocess': force_reprocess,
        'error': None,
        'pipeline_result': None,
    }
    with _upload_jobs_lock:
        _cleanup_upload_jobs_locked(now_ts)
        _upload_jobs[job_id] = record
        logger.info(f"Created upload job in memory: {job_id}")

    _upload_job_queue.put({'job_id': job_id})
    return job_id


def _upload_worker_loop(worker_name: str) -> None:
    """Worker loop consuming queued upload jobs from memory queue."""
    logger.info(f"Upload worker started: {worker_name}")
    
    while True:
        try:
            # Get job from memory queue (blocking with timeout)
            task = _upload_job_queue.get(timeout=5)
            job_id = task.get('job_id') if isinstance(task, dict) else None
            
            if not job_id:
                _upload_job_queue.task_done()
                continue
            
            logger.info(f"{worker_name}: Processing job {job_id}")
            
            # Get job details from memory
            with _upload_jobs_lock:
                job = _upload_jobs.get(job_id)
                if not job:
                    logger.warning(f"{worker_name}: Job {job_id} not found")
                    _upload_job_queue.task_done()
                    continue
                
                # Mark as processing
                job['status'] = 'processing'
                job['started_at'] = datetime.now().isoformat()
            
            # Process the CV
            try:
                pipeline_result = process_source_cv(
                    cv_path=Path(job['upload_path']),
                    job_description=job.get('job_description'),
                    force_reprocess=bool(job.get('force_reprocess')),
                    llm_runtime_config=job.get('llm_runtime_config') or {}
                )
                
                # Update job status
                with _upload_jobs_lock:
                    mem_job = _upload_jobs.get(job_id)
                    if mem_job:
                        if pipeline_result.get('success'):
                            mem_job['status'] = 'completed'
                            mem_job['pipeline_result'] = pipeline_result
                            mem_job['error'] = None
                            
                            # Invalidate search cache when new candidate is added
                            try:
                                from redis_cache import invalidate_search_cache
                                deleted = invalidate_search_cache()
                                if deleted > 0:
                                    logger.info(f"✓ Invalidated {deleted} search cache entries after new candidate upload")
                            except Exception as cache_err:
                                logger.warning(f"Could not invalidate search cache: {cache_err}")
                        else:
                            mem_job['status'] = 'failed'
                            mem_job['error'] = pipeline_result.get('error', 'CV processing failed')
                        mem_job['completed_ts'] = time.time()
                        mem_job['completed_at'] = datetime.now().isoformat()
                
                logger.info(f"{worker_name}: Completed job {job_id}")
                
            except Exception as e:
                logger.error(f"{worker_name}: Job {job_id} failed: {e}", exc_info=True)
                
                with _upload_jobs_lock:
                    mem_job = _upload_jobs.get(job_id)
                    if mem_job:
                        mem_job['status'] = 'failed'
                        mem_job['error'] = str(e)
                        mem_job['completed_ts'] = time.time()
                        mem_job['completed_at'] = datetime.now().isoformat()
            
            finally:
                _upload_job_queue.task_done()
                
        except queue.Empty:
            # No jobs available, continue waiting
            continue
        except Exception as e:
            logger.error(f"Unhandled upload worker error ({worker_name}): {e}", exc_info=True)


def _ensure_upload_workers_started() -> None:
    """Start upload workers once for this process."""
    global _upload_workers_started
    if _upload_workers_started:
        return

    with _upload_jobs_lock:
        if _upload_workers_started:
            return
        for i in range(_UPLOAD_WORKER_COUNT):
            worker = threading.Thread(
                target=_upload_worker_loop,
                args=(f'upload-worker-{i+1}',),
                daemon=True
            )
            worker.start()
        _upload_workers_started = True


@app.before_request
def _lazy_start_upload_workers():
    _ensure_upload_workers_started()


def compute_local_keyword_match(cv_text: str, job_description: str) -> Dict[str, Any]:
    """Lightweight keyword match used when enhanced triage is unavailable."""
    stop_words = {
        'about', 'after', 'again', 'also', 'and', 'are', 'been', 'being', 'build',
        'candidate', 'candidates', 'experience', 'good', 'have', 'into', 'knowledge',
        'must', 'need', 'plus', 'role', 'should', 'skills', 'strong', 'team',
        'their', 'they', 'this', 'using', 'with', 'years'
    }
    tokens = re.findall(r'[a-zA-Z0-9+#./-]{2,}', job_description.lower())
    keywords = []
    seen = set()
    for token in tokens:
        if token in stop_words:
            continue
        if token not in seen:
            seen.add(token)
            keywords.append(token)

    cv_lower = cv_text.lower()
    matched = [keyword for keyword in keywords if keyword in cv_lower]
    score = round((len(matched) / len(keywords)) * 100, 1) if keywords else 0.0

    return {
        'match_percentage': score,
        'matched_keywords': matched[:15],
        'reason': f"Matched {len(matched)} of {len(keywords)} extracted JD keywords"
    }


def _tokenize_for_matching(text: str) -> List[str]:
    """Tokenize text into normalized terms used for ranking."""
    if not text:
        return []
    return re.findall(r'[a-zA-Z0-9+#./-]{2,}', text.lower())


def _extract_min_years_requirement(job_description: str) -> Optional[float]:
    """Extract minimum years requirement from JD when explicitly mentioned."""
    if not job_description:
        return None
    patterns = [
        r'(\d+(?:\.\d+)?)\s*\+?\s*years?',
        r'min(?:imum)?\s*(\d+(?:\.\d+)?)\s*years?',
        r'(\d+(?:\.\d+)?)\s*yrs?'
    ]
    for pattern in patterns:
        match = re.search(pattern, job_description.lower())
        if match:
            try:
                return float(match.group(1))
            except Exception:
                return None
    return None


_KNOWN_TECH_SKILLS = {
    # Languages
    'python', 'typescript', 'javascript', 'java', 'c++', 'c#', 'go', 'golang', 'rust', 'php',
    'ruby', 'scala', 'kotlin', 'swift', 'r',
    # Frontend / Web
    'html', 'css', 'sass', 'scss', 'less', 'tailwind', 'bootstrap',
    'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'gatsby',
    'webpack', 'vite', 'jquery', 'redux', 'zustand', 'responsive design',
    # Backend frameworks
    'django', 'flask', 'fastapi', 'node', 'nodejs', 'express',
    'spring', 'spring boot', '.net', 'rails',
    # Mobile
    'react native', 'flutter', 'ionic', 'xamarin', 'android', 'ios',
    # Databases
    'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'nosql',
    'cassandra', 'dynamodb', 'sqlite', 'oracle',
    # Cloud / DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'github',
    'git', 'ci/cd',
    # Data Science / ML
    'pandas', 'numpy', 'scikit-learn', 'spark', 'airflow', 'mlflow',
    'tensorflow', 'pytorch', 'keras', 'power bi', 'tableau',
    'machine learning', 'deep learning', 'data science', 'nlp', 'llm', 'openai',
    # Architecture
    'system design', 'rest api', 'restful', 'microservices', 'graphql',
    # QA
    'selenium',
    # Product tooling
    'jira',
    # Integration / Middleware
    'mulesoft', 'salesforce', 'sap', 'anypoint', 'tibco', 'informatica',
    # Other
    'kafka', 'rabbitmq', 'linux', 'nginx', 'apache', 'figma',
}

# Common abbreviations and aliases that should map to canonical skill names
_SKILL_ALIASES = {
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'k8s': 'kubernetes',
    'tf': 'terraform',
    'node.js': 'nodejs',
    'react.js': 'react',
    'vue.js': 'vue',
    'angular.js': 'angular',
    'angularjs': 'angular',
    'pg': 'postgresql',
    'postgres': 'postgresql',
    'mongo': 'mongodb',
    'es': 'elasticsearch',
}


# Some JDs list paired platform/framework options using "and" even when they
# clearly mean either/or. Collapse these into OR-groups to avoid overly strict
# critical-skill gating (especially when len(critical_skills) <= 2).
_CRITICAL_SKILL_OR_GROUPS = [
    {'ios', 'android'},
    {'swift', 'kotlin'},
    {'react native', 'flutter'},
    {'tensorflow', 'pytorch'},
]


def _skills_share_or_group(skill_a: str, skill_b: str) -> bool:
    a = (skill_a or '').strip().lower()
    b = (skill_b or '').strip().lower()
    if not a or not b or a == b:
        return False
    for group in _CRITICAL_SKILL_OR_GROUPS:
        if a in group and b in group:
            return True
    return False


def _extract_critical_jd_skills(job_description: str) -> List[str]:
    """Extract explicit must-have skills from JD text for stronger ranking separation."""
    if not job_description:
        return []

    jd_lower = job_description.lower()

    # Prefer extracting from *required* clauses only.
    # This prevents "preferred/bonus/good-to-have" terms from becoming hard gates.
    optional_markers = [
        'good to have', 'nice to have', 'preferred', 'preference', 'bonus', 'plus', 'a plus'
    ]
    required_markers = [
        'must', 'must have', 'required', 'need', 'looking for', 'should', 'strong in',
        'experience in', 'hands-on', 'hands on', 'proficient in'
    ]
    parts = [p.strip() for p in re.split(r'[\n\r\.]+', jd_lower) if p.strip()]
    required_parts = [
        p for p in parts
        if any(m in p for m in required_markers) and not any(m in p for m in optional_markers)
    ]
    jd_required = ' '.join(required_parts) if required_parts else jd_lower
    found: List[str] = []

    # First pass: resolve aliases (e.g. JS -> javascript, TS -> typescript)
    for alias, canonical in _SKILL_ALIASES.items():
        if re.search(rf'\b{re.escape(alias)}\b', jd_required):
            found.append(canonical)

    # Second pass: match known tech skills directly
    for skill in sorted(_KNOWN_TECH_SKILLS, key=len, reverse=True):
        if re.search(rf'\b{re.escape(skill)}\b', jd_required):
            found.append(skill)

    phrase_patterns = [
        r'(?:experience in|strong in|must have|hands[- ]on(?: experience)? with|proficient in)\s+([^.;\n]+)',
        r'(?:looking for|need|required)\s+([^.;\n]+)'
    ]
    splitter = re.compile(r',|/|\band\b|\bor\b|&', re.IGNORECASE)
    for pattern in phrase_patterns:
        for match in re.finditer(pattern, jd_required):
            phrase = (match.group(1) or '').strip()
            if not phrase:
                continue
            for chunk in splitter.split(phrase):
                token = re.sub(r'[^a-z0-9+#./\-\s]', ' ', chunk).strip()
                token = re.sub(r'\s+', ' ', token)
                # Check aliases first
                if token in _SKILL_ALIASES:
                    found.append(_SKILL_ALIASES[token])
                elif token in _KNOWN_TECH_SKILLS:
                    found.append(token)

    deduped: List[str] = []
    seen = set()
    for skill in found:
        key = skill.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(key)

    # Remove shadowed shorter skills when a more specific multi-word skill exists.
    # Example: avoid extracting both "react native" and "react" as separate critical skills.
    deduped_sorted = sorted(deduped, key=len, reverse=True)
    kept: List[str] = []
    for skill in deduped_sorted:
        shadowed = False
        for longer in kept:
            if ' ' not in longer:
                continue
            if re.search(rf'(?<!\w){re.escape(skill)}(?!\w)', longer):
                shadowed = True
                break
        if not shadowed:
            kept.append(skill)
    deduped = kept

    # Collapse common "A/B" or "A or B" patterns into a single OR-group token.
    # Also handle select "A and B" pairings that are commonly used to mean either/or.
    # Example: "iOS and Android" or "Swift and Kotlin" often mean mobile coverage,
    # not that every candidate must have both.
    collapsed: List[str] = []
    used = set()
    for idx, s1 in enumerate(deduped):
        if s1 in used:
            continue

        grouped = False
        for s2 in deduped[idx + 1:]:
            if s2 in used:
                continue

            # Only collapse when the JD explicitly expresses an alternative.
            # For "and/&", only treat as alternative if the pair belongs to a known OR-group.
            if (
                re.search(rf'\b{re.escape(s1)}\b\s*(?:/|\bor\b)\s*\b{re.escape(s2)}\b', jd_required)
                or re.search(rf'\b{re.escape(s2)}\b\s*(?:/|\bor\b)\s*\b{re.escape(s1)}\b', jd_required)
                or (
                    _skills_share_or_group(s1, s2)
                    and (
                        re.search(rf'\b{re.escape(s1)}\b\s*(?:\band\b|&)\s*\b{re.escape(s2)}\b', jd_required)
                        or re.search(rf'\b{re.escape(s2)}\b\s*(?:\band\b|&)\s*\b{re.escape(s1)}\b', jd_required)
                    )
                )
            ):
                collapsed.append(f"{s1}|{s2}")
                used.add(s1)
                used.add(s2)
                grouped = True
                break

        if not grouped:
            collapsed.append(s1)

    return collapsed[:8]


def _extract_domain_terms_from_jd(job_description: str) -> List[str]:
    """Dynamically extract domain/industry terms from a JD for matching against candidate domains.

    Instead of a tiny hardcoded list, this scans for a comprehensive set of domain
    phrases that appear in real-world JDs and returns only those present.
    """
    if not job_description:
        return []

    jd_lower = job_description.lower()

    # Comprehensive domain vocabulary covering common industry sectors
    _DOMAIN_VOCABULARY = [
        # Data & AI
        'data science', 'data analytics', 'data engineering', 'machine learning',
        'deep learning', 'artificial intelligence', 'natural language processing',
        'computer vision', 'big data', 'business intelligence',
        # Web / Software
        'web development', 'frontend', 'front-end', 'backend', 'back-end',
        'full stack', 'full-stack', 'software engineering', 'software development',
        # Mobile
        'mobile development', 'android', 'ios',
        # Cloud & Infra
        'cloud', 'cloud computing', 'devops', 'site reliability',
        'infrastructure', 'platform engineering',
        # Databases
        'database', 'data management', 'data warehousing', 'etl',
        # Security
        'cybersecurity', 'information security', 'network security',
        # Industry verticals
        'fintech', 'healthcare', 'e-commerce', 'ecommerce', 'banking',
        'insurance', 'automotive', 'embedded systems', 'iot',
        'telecommunications', 'media', 'gaming', 'edtech', 'logistics',
        'supply chain', 'manufacturing', 'retail', 'real estate',
        # General tech domains
        'api development', 'microservices', 'distributed systems',
        'enterprise', 'saas', 'erp', 'crm',
        'testing', 'quality assurance', 'automation',
        'ui/ux', 'user experience', 'product development',
        'blockchain', 'web3',
        # Python ecosystem common in JDs
        'python', 'analytics',
    ]

    found = [term for term in _DOMAIN_VOCABULARY if term in jd_lower]

    # Deduplicate overlapping terms (e.g. "data science" and "data")
    deduped: List[str] = []
    seen = set()
    for term in found:
        key = term.strip()
        if key not in seen:
            seen.add(key)
            deduped.append(key)

    return deduped


def _extract_target_seniority(job_description: str) -> Optional[int]:
    """Infer target seniority level from JD terms."""
    if not job_description:
        return None

    jd = job_description.lower()
    seniority_map = {
        'entry': 1,
        'junior': 1,
        'mid': 2,
        'senior': 3,
        'lead': 4,
        'staff': 4,
        'manager': 4,
        'principal': 5,
        'architect': 5,
        'executive': 5,
    }

    hits = [level for term, level in seniority_map.items() if re.search(rf'\b{re.escape(term)}\b', jd)]
    return max(hits) if hits else None


def _candidate_seniority_value(candidate: Dict[str, Any]) -> int:
    """Convert candidate seniority into an ordered numeric scale."""
    value = str(candidate.get('seniority_level') or candidate.get('career_level') or '').strip().upper()
    mapping = {
        'ENTRY': 1,
        'JUNIOR': 1,
        'MID': 2,
        'SENIOR': 3,
        'LEAD': 4,
        'EXECUTIVE': 5,
    }
    return mapping.get(value, 0)


def _best_knowledge_summary(candidate: Dict[str, Any]) -> str:
    """Build a concise recruiter-facing summary of strongest knowledge areas."""
    skills = [
        str(s).strip() for s in (
            (candidate.get('core_technical_skills') or [])
            + (candidate.get('secondary_technical_skills') or [])
            + (candidate.get('frameworks_tools') or [])
        ) if str(s).strip()
    ]
    strengths = [str(s).strip() for s in (candidate.get('key_strengths') or []) if str(s).strip()]

    top_skills: List[str] = []
    seen = set()
    for skill in skills:
        key = skill.lower()
        if key in seen:
            continue
        seen.add(key)
        top_skills.append(skill)
        if len(top_skills) >= 5:
            break

    top_strengths = strengths[:2]
    parts = []
    if top_skills:
        parts.append(f"Core strengths: {', '.join(top_skills)}")
    if top_strengths:
        parts.append(f"Evidence: {'; '.join(top_strengths)}")
    return ' | '.join(parts)


def _capability_focus_score(jd_text: str, strength_text: str) -> float:
    """Score whether candidate capability cues align with the role intent in JD."""
    jd = jd_text.lower()
    strengths = strength_text.lower()

    focus_map = _FOCUS_KEYWORDS

    jd_hits = []
    candidate_hits = []
    for key, phrases in focus_map.items():
        if any(phrase in jd for phrase in phrases):
            jd_hits.append(key)
        if any(phrase in strengths for phrase in phrases):
            candidate_hits.append(key)

    if not jd_hits:
        return 35.0

    overlap = len(set(jd_hits).intersection(candidate_hits))
    return round((overlap / len(set(jd_hits))) * 100.0, 2)


# Focus/role keywords used for lightweight intent gating and capability scoring.
_FOCUS_KEYWORDS = {
    'case_study': ['case study', 'hypothesis', 'ab test', 'a/b test', 'experiment', 'analytics', 'business problem'],
    'problem_solving': ['problem solving', 'complex problem', 'reasoning', 'debugging', 'troubleshooting'],
    'dsa': ['dsa', 'data structure', 'algorithm', 'leetcode', 'competitive programming'],
    'ml_data': [
        'machine learning', 'deep learning', 'modeling', 'model building', 'statistics', 'data science',
        'feature engineering', 'predictive model', 'neural network', 'nlp', 'computer vision',
        'pytorch', 'tensorflow', 'mlops', 'model deployment', 'model optimization'
    ],
    'backend_platform': ['backend', 'api', 'apis', 'microservice', 'microservices', 'system design', 'scalability',
                         'restful', 'rest api', 'server-side', 'server side'],
    'frontend_ui': ['frontend', 'front-end', 'front end', 'ui development', 'user interface',
                    'responsive design', 'single page', 'spa', 'component', 'css', 'html', 'react', 'angular', 'vue'],
    'fullstack': ['full stack', 'full-stack', 'fullstack', 'end-to-end', 'end to end'],
    'data_viz': ['data visualization', 'dashboard', 'power bi', 'tableau', 'reporting',
                 'business intelligence', 'bi tool', 'charts', 'grafana', 'excel'],
    'devops_infra': ['devops', 'ci/cd', 'ci cd', 'pipeline', 'pipelines', 'infrastructure', 'deployment',
                     'containerization', 'orchestration', 'docker', 'kubernetes', 'terraform',
                     'observability'],
    'database': ['database', 'sql', 'nosql', 'data modeling', 'schema design',
                 'query optimization', 'data extraction', 'etl', 'data pipeline'],
    'cloud': ['cloud', 'aws', 'azure', 'gcp', 'serverless', 'lambda', 'cloud platform', 'scaling'],
    'mobile': ['mobile', 'android', 'ios', 'react native', 'flutter', 'swift', 'kotlin'],
    'security': [
        'cybersecurity', 'security analyst', 'vulnerability', 'vulnerabilities', 'vulnerability testing',
        'penetration testing', 'incident response', 'siem', 'soc analyst'
    ],
    'qa_testing': ['qa', 'qa tester', 'tester', 'test automation', 'automation testing', 'manual testing',
                   'selenium', 'test case', 'test cases', 'quality assurance'],
    'recruiting': ['recruiter', 'recruitment', 'sourcing', 'screening', 'linkedin', 'job portal', 'coordination', 'talent acquisition'],
    'product': ['product manager', 'product management', 'roadmap', 'backlog',
                'user story', 'user stories', 'prd', 'product strategy', 'prioritize features', 'prioritise features'],
    'leadership': ['leadership', 'mentoring', 'team management', 'stakeholder', 'cross-functional']
}


# Focus keys that represent concrete roles/capabilities for gating.
# Avoid using broad buckets like leadership/problem-solving as gates.
_ROLE_FOCUS_KEYS = {
    'ml_data', 'backend_platform', 'frontend_ui', 'fullstack', 'data_viz',
    'devops_infra', 'database', 'cloud', 'mobile', 'security', 'qa_testing',
    'recruiting', 'product'
}


# Some roles are especially prone to semantic leakage (e.g., embedded/infra candidates
# matching “security” or “product” JDs due to one generic phrase). Require stronger
# evidence (multiple distinct phrase hits) before treating them as true focus overlap.
_FOCUS_MIN_DISTINCT_PHRASE_HITS: Dict[str, int] = {
    'security': 2,
    'product': 2,
    'recruiting': 2,
}


def _extract_focus_hit_counts(text: str) -> Dict[str, int]:
    """Return focus keys mapped to the number of distinct phrases matched in text."""
    if not text:
        return {}
    lower = text.lower()
    counts: Dict[str, int] = {}
    for key, phrases in _FOCUS_KEYWORDS.items():
        matched = 0
        for phrase in phrases:
            if re.search(rf'(?<!\w){re.escape(phrase)}(?!\w)', lower):
                matched += 1
        if matched:
            counts[key] = matched
    return counts


def _extract_focus_hits(text: str) -> List[str]:
    """Return focus keys that appear in the given text (lowercased substring match)."""
    if not text:
        return []
    return list(_extract_focus_hit_counts(text).keys())


def compute_semantic_candidate_match(
    candidate: Dict[str, Any],
    jd_embedding: List[float],
    job_description: str
) -> Dict[str, Any]:
    """
    Compute semantic similarity between candidate and JD using vector embeddings.
    This provides TRUE contextual understanding, not just keyword matching.
    """
    import json
    from vector_search import get_vector_search_engine
    
    # Get candidate embedding
    candidate_embedding = candidate.get('embedding')
    
    # Parse embedding if it's stored as JSON string
    if candidate_embedding and isinstance(candidate_embedding, str):
        try:
            candidate_embedding = json.loads(candidate_embedding)
        except Exception as e:
            logger.warning(f"Could not parse embedding string: {e}")
            candidate_embedding = None
    
    if not candidate_embedding:
        # Generate embedding from candidate data (NO fallback to keyword matching)
        try:
            engine = get_vector_search_engine()
            candidate_text = engine.build_embedding_text(candidate)
            candidate_embedding = engine.generate_embedding(candidate_text)
        except Exception as e:
            logger.error(f"Could not generate embedding for candidate: {e}")
            # Return error - NO fallback to keyword matching
            raise ValueError(f"Semantic ranking requires embeddings. Candidate embedding generation failed: {e}")
    
    # Compute semantic similarity (contextual understanding)
    try:
        engine = get_vector_search_engine()
        similarity = engine.cosine_similarity(jd_embedding, candidate_embedding)
    except Exception as e:
        logger.error(f"Could not compute similarity: {e}")
        # Return error - NO fallback to keyword matching
        raise ValueError(f"Semantic ranking requires similarity computation. Failed: {e}")
    
    # Convert to percentage (0-100)
    semantic_score = round(similarity * 100, 2)
    
    # Extract critical skills for additional validation
    critical_skills = _extract_critical_jd_skills(job_description)
    candidate_skills = (
        (candidate.get('core_technical_skills') or []) +
        (candidate.get('secondary_technical_skills') or []) +
        (candidate.get('frameworks_tools') or [])
    )
    
    all_skills_lower = [str(s).lower() for s in candidate_skills if str(s).strip()]
    all_skill_blob = " ".join(all_skills_lower)

    # Candidate text used for critical-skill matching should include domains and summaries,
    # not only structured skills, because extraction quality varies per CV.
    candidate_skill_match_blob = " ".join(
        [
            all_skill_blob,
            str(candidate.get('primary_domain') or ''),
            " ".join([str(d) for d in (candidate.get('secondary_domains') or [])]),
            " ".join([str(d) for d in (candidate.get('domain_expertise') or [])]),
            str(candidate.get('cleaned_narrative') or ''),
            str(candidate.get('verdict_reason') or ''),
            " ".join([str(s) for s in (candidate.get('key_strengths') or [])]),
        ]
    ).lower()
    
    matched_critical = []
    for skill in critical_skills:
        if '|' in skill:
            alts = [s.strip() for s in skill.split('|') if s.strip()]
            if any(re.search(rf'\b{re.escape(alt)}\b', candidate_skill_match_blob) for alt in alts):
                matched_critical.append(skill)
        else:
            if re.search(rf'\b{re.escape(skill)}\b', candidate_skill_match_blob):
                matched_critical.append(skill)
    
    if critical_skills:
        critical_coverage = round((len(matched_critical) / len(critical_skills)) * 100.0, 2)
    else:
        # No explicit critical skills found in the JD. Treat as "no critical gating",
        # and avoid inflating scores by pretending coverage is 100%.
        critical_coverage = None
    
    # Determine minimum critical coverage threshold
    if len(critical_skills) <= 2:
        if critical_skills and any('|' in s for s in critical_skills):
            # If the JD expresses alternatives (OR-groups), don't require matching *every*
            # OR-group. Matching at least one is often a valid fit for terse JDs.
            minimum_critical_coverage = 50.0
        else:
            minimum_critical_coverage = 100.0 if critical_skills else 0.0
    else:
        # Messy JDs often list many skills; keep gating realistic.
        minimum_critical_coverage = 60.0
    
    # Blend semantic similarity with critical skills *only if* we extracted explicit
    # critical skills from the JD. Otherwise, use pure semantic score.
    if critical_skills and critical_coverage is not None:
        # Keep semantic dominant; critical skills nudge ranking but shouldn't zero out.
        final_score = round(
            0.70 * semantic_score +
            0.30 * critical_coverage,
            2
        )
    else:
        final_score = semantic_score
    
    missing_critical = [s for s in critical_skills if s not in matched_critical]
    if critical_skills and critical_coverage is not None and critical_coverage <= 25.0:
        # Mild downweight when we extracted clear critical skills and the candidate matches almost none.
        final_score = round(final_score * 0.80, 2)
    
    selection_basis = (
        f"Semantic match with {len(matched_critical)}/{len(critical_skills)} critical skills"
        if critical_skills
        else "Semantic contextual match"
    )

    # --- Role-intent sanity check (prevents generic JDs returning random roles) ---
    # If the JD has a clear intent (e.g., security/recruiting/product/qa/devops/etc),
    # require the candidate profile to show *some* overlapping intent signal.
    jd_focus_counts = _extract_focus_hit_counts(job_description)
    jd_focus = set(jd_focus_counts.keys()).intersection(_ROLE_FOCUS_KEYS)
    if jd_focus:
        candidate_focus_text = " ".join(
            [
                str(candidate.get('primary_domain') or ''),
                " ".join([str(d) for d in (candidate.get('secondary_domains') or [])]),
                " ".join([str(d) for d in (candidate.get('domain_expertise') or [])]),
                all_skill_blob,
                candidate.get('cleaned_narrative') or '',
                candidate.get('verdict_reason') or '',
                " ".join(candidate.get('key_strengths') or []),
            ]
        )
        candidate_focus_counts = _extract_focus_hit_counts(candidate_focus_text)
        candidate_focus = set(candidate_focus_counts.keys()).intersection(_ROLE_FOCUS_KEYS)

        # Apply per-role minimum distinct phrase hits before considering a key as true overlap.
        candidate_focus_strong = {
            k
            for k in candidate_focus
            if candidate_focus_counts.get(k, 0) >= _FOCUS_MIN_DISTINCT_PHRASE_HITS.get(k, 1)
        }

        if jd_focus.isdisjoint(candidate_focus_strong):
            # Heavy penalty: off-role candidates should drop below UI thresholds.
            final_score = round(final_score * 0.45, 2)

    return {
        'match_percentage': final_score,
        'semantic_score': semantic_score,
        'critical_skill_coverage': critical_coverage,
        'critical_skill_min_required': minimum_critical_coverage,
        'critical_skills_required': critical_skills,
        'critical_skills_matched': matched_critical,
        'critical_skills_missing': missing_critical,
        'matched_keywords': matched_critical,  # For compatibility
        'selection_basis': selection_basis,
        'best_knowledge': _best_knowledge_summary(candidate),
        'reason': f"Semantic similarity: {semantic_score}%, Critical skills: {critical_coverage}%",
    }


def compute_intelligent_candidate_match(candidate: Dict[str, Any], job_description: str, cv_text: str) -> Dict[str, Any]:
    """Compute weighted candidate ranking beyond plain keyword matching."""
    keyword_match = compute_local_keyword_match(cv_text, job_description)

    jd_text = job_description or ''
    jd_tokens = set(_tokenize_for_matching(jd_text))
    candidate_tokens = set(_tokenize_for_matching(cv_text))
    token_overlap = len(jd_tokens.intersection(candidate_tokens))
    token_score = round((token_overlap / len(jd_tokens)) * 100.0, 2) if jd_tokens else 0.0

    core_skills = [str(s).strip() for s in (candidate.get('core_technical_skills') or []) if str(s).strip()]
    secondary_skills = [str(s).strip() for s in (candidate.get('secondary_technical_skills') or []) if str(s).strip()]
    framework_skills = [str(s).strip() for s in (candidate.get('frameworks_tools') or []) if str(s).strip()]
    all_skills_lower = [s.lower() for s in core_skills + secondary_skills + framework_skills]
    all_skill_blob = " ".join(all_skills_lower)

    critical_skills = _extract_critical_jd_skills(jd_text)
    matched_critical_skills = []
    for skill in critical_skills:
        if '|' in skill:
            alts = [s.strip() for s in skill.split('|') if s.strip()]
            if any(re.search(rf'\b{re.escape(alt)}\b', all_skill_blob) for alt in alts):
                matched_critical_skills.append(skill)
        else:
            if re.search(rf'\b{re.escape(skill)}\b', all_skill_blob):
                matched_critical_skills.append(skill)
    critical_coverage = round((len(matched_critical_skills) / len(critical_skills)) * 100.0, 2) if critical_skills else 0.0
    if len(critical_skills) <= 2:
        minimum_critical_coverage = 100.0 if critical_skills else 0.0
    else:
        minimum_critical_coverage = 67.0

    jd_skill_terms = [token for token in jd_tokens if len(token) >= 3]
    if jd_skill_terms:
        exact_skill_hits = sum(1 for term in jd_skill_terms if any(term == skill for skill in all_skills_lower))
        fuzzy_skill_hits = sum(1 for term in jd_skill_terms if any(term in skill for skill in all_skills_lower))
        skill_score = round(((2 * exact_skill_hits + fuzzy_skill_hits) / (3 * len(jd_skill_terms))) * 100.0, 2)
        skill_score = min(skill_score, 100.0)
    else:
        skill_score = keyword_match['match_percentage']

    strength_bits = [
        candidate.get('verdict_reason') or '',
        " ".join(candidate.get('key_strengths') or []),
        " ".join(candidate.get('matched_requirements') or []),
    ]
    fitment = candidate.get('fitment_analysis') or []
    if isinstance(fitment, list):
        for entry in fitment:
            if isinstance(entry, dict):
                strength_bits.append(str(entry.get('category') or ''))
                strength_bits.append(str(entry.get('candidate_profile') or ''))

    strength_text = " ".join(strength_bits)
    capability_score = _capability_focus_score(jd_text, strength_text)

    min_years = _extract_min_years_requirement(jd_text)
    years = candidate.get('years_experience')
    if years is None:
        years = candidate.get('years_of_experience')
    years = float(years or 0)
    if min_years is None:
        experience_score = min(100.0, 45.0 + (years * 5.0)) if years > 0 else 25.0
    elif years >= min_years:
        experience_score = min(100.0, 80.0 + ((years - min_years) * 4.0))
    else:
        experience_score = max(0.0, (years / max(min_years, 0.5)) * 55.0)

    target_seniority = _extract_target_seniority(jd_text)
    candidate_seniority = _candidate_seniority_value(candidate)
    if target_seniority is None:
        seniority_score = 55.0 if candidate_seniority > 0 else 35.0
    elif candidate_seniority >= target_seniority:
        seniority_score = 100.0
    else:
        shortfall = target_seniority - candidate_seniority
        seniority_score = max(0.0, 75.0 - (shortfall * 30.0))

    domain_text = " ".join(
        [
            str(candidate.get('primary_domain') or ''),
            " ".join([str(d) for d in (candidate.get('secondary_domains') or [])]),
            " ".join([str(d) for d in (candidate.get('domain_expertise') or [])]),
            " ".join([str(s).lower() for s in (candidate.get('core_technical_skills') or [])]),
            " ".join([str(s).lower() for s in (candidate.get('secondary_technical_skills') or [])]),
            candidate.get('cleaned_narrative') or '',
        ]
    ).lower()
    jd_domain_hits = _extract_domain_terms_from_jd(jd_text)
    if not jd_domain_hits:
        domain_score = 45.0
    else:
        domain_score = round(
            (sum(1 for term in jd_domain_hits if term in domain_text) / len(jd_domain_hits)) * 100.0,
            2
        )

    final_score = round(
        (0.40 * (critical_coverage if critical_skills else skill_score)) +
        (0.18 * skill_score) +
        (0.12 * capability_score) +
        (0.12 * token_score) +
        (0.10 * experience_score) +
        (0.08 * seniority_score),
        2
    )

    if critical_skills and critical_coverage < 100.0:
        if critical_coverage < 50.0:
            final_score = round(final_score * 0.45, 2)
        else:
            final_score = round(final_score * 0.75, 2)

    missing_critical_skills = [skill for skill in critical_skills if skill not in matched_critical_skills]
    selection_basis = (
        f"Selected for {len(matched_critical_skills)}/{len(critical_skills)} critical skills"
        if critical_skills
        else "Selected on weighted skill, capability, and experience fit"
    )

    return {
        'match_percentage': final_score,
        'matched_keywords': keyword_match['matched_keywords'],
        'reason': (
            f"Weighted fit: critical={critical_coverage if critical_skills else skill_score:.1f}, "
            f"skills={skill_score:.1f}, capability={capability_score:.1f}, "
            f"experience={experience_score:.1f}, seniority={seniority_score:.1f}."
        ),
        'selection_basis': selection_basis,
        'critical_skills_required': critical_skills,
        'critical_skills_matched': matched_critical_skills,
        'critical_skills_missing': missing_critical_skills,
        'critical_skill_coverage': critical_coverage,
        'critical_skill_min_required': minimum_critical_coverage,
        'best_knowledge': _best_knowledge_summary(candidate)
    }


def _candidate_has_searchable_signal(intel: Dict[str, Any]) -> bool:
    """Filter out placeholder or unusable records from UI search results."""
    skills = (
        intel.get('core_technical_skills')
        or intel.get('secondary_technical_skills')
        or intel.get('key_skills')
        or []
    )
    domain = (intel.get('primary_domain') or '').strip()
    years = intel.get('years_experience')
    if years is None:
        years = intel.get('years_of_experience')

    return bool(
        skills or
        domain or
        (isinstance(years, (int, float)) and years > 0)
    )

@app.route('/')
def index():
    """Render unified interface by default; allow redactor-only mode via query."""
    mode = request.args.get('mode', '').strip().lower()
    if mode in {'redactor', 'cv-redactor', 'redaction'}:
        try:
            return render_template('index.html')
        except:
            return landing_page()
    try:
        return render_template('index_new.html')
    except:
        return landing_page()

@app.route('/landing')
def landing_page():
    """Simple landing page when templates are not available"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CV Intelligence System</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 { color: #333; margin-bottom: 10px; }
            h2 { color: #667eea; margin-top: 30px; }
            .status { padding: 15px; background: #e8f5e9; border-radius: 8px; margin: 20px 0; }
            .status.error { background: #ffebee; }
            a { color: #667eea; text-decoration: none; font-weight: 600; }
            a:hover { text-decoration: underline; }
            ul { line-height: 2; }
            .api-link { 
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border-radius: 8px;
                margin: 10px 10px 10px 0;
            }
            .api-link:hover { background: #5568d3; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 CV Intelligence System</h1>
            <p><strong>Status:</strong> ✅ Running</p>
            
            <div class="status">
                <strong>⚠️ Templates Not Found</strong><br>
                The HTML templates are missing. Using API-only mode.
            </div>
            
            <h2>📡 Available API Endpoints:</h2>
            <a href="/health" class="api-link">Health Check</a>
            <a href="/api/connection-status" class="api-link">Connection Status</a>
            <a href="/api/statistics" class="api-link">Statistics</a>
            
            <h2>🔧 How to Fix:</h2>
            <ol>
                <li>Ensure <code>templates/</code> folder is in your repository</li>
                <li>Check that templates are not in <code>.gitignore</code></li>
                <li>Redeploy on Render</li>
            </ol>
            
            <h2>📚 API Usage:</h2>
            <ul>
                <li><strong>POST /api/redact</strong> - Redact a CV</li>
                <li><strong>POST /upload</strong> - Upload and process CV</li>
                <li><strong>POST /api/search</strong> - Search candidates</li>
                <li><strong>GET /api/statistics</strong> - Get statistics</li>
                <li><strong>GET /health</strong> - Health check</li>
            </ul>
            
            <h2>🔗 Repository:</h2>
            <p><a href="https://github.com/Shivanikinagi/CV-redactor" target="_blank">
                https://github.com/Shivanikinagi/CV-redactor
            </a></p>
            
            <p style="margin-top: 40px; color: #666; font-size: 14px;">
                CV Intelligence System v1.0.0
            </p>
        </div>
    </body>
    </html>
    """
    return html


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'templates_available': os.path.exists('templates'),
        'supabase_configured': is_supabase_configured(),
        'llm_configured': bool(os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY'))
    })

@app.route('/redactor')
def redactor_page():
    """Render the standalone CV redactor page."""
    return render_template('index.html')

@app.route('/semantic-search')
def semantic_search_page():
    """Render the semantic search page"""
    return render_template('semantic_search.html')

def _check_duplicate_upload(file_content: bytes, filename: str) -> dict:
    """
    Check if this file was already uploaded by computing its hash.
    Returns dict with 'is_duplicate', 'existing_candidate', 'hash'
    """
    import hashlib
    
    # Compute file hash
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Check if this hash exists in database
    storage = get_supabase_storage()
    if not storage:
        # If Supabase is down, allow upload (better than blocking)
        return {'is_duplicate': False, 'hash': file_hash}
    
    try:
        # Query for existing candidate with this hash
        response = storage.client.table('cv_intelligence').select(
            'anonymized_id, created_at, years_experience, primary_domain, core_technical_skills'
        ).eq('original_cv_hash', file_hash).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            existing = response.data[0]
            return {
                'is_duplicate': True,
                'hash': file_hash,
                'existing_candidate': {
                    'anonymized_id': existing.get('anonymized_id'),
                    'created_at': existing.get('created_at'),
                    'years_experience': existing.get('years_experience'),
                    'primary_domain': existing.get('primary_domain'),
                    'core_skills': existing.get('core_technical_skills', [])[:3]
                }
            }
        
        return {'is_duplicate': False, 'hash': file_hash}
        
    except Exception as e:
        logger.warning(f"Duplicate check failed: {e}")
        # On error, allow upload (better than blocking)
        return {'is_duplicate': False, 'hash': file_hash}


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload; queue async processing by default and support optional sync mode."""
    try:
        # Check if file is present
        if 'cv_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['cv_file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PDF or DOCX files'}), 400
        
        # Read file content for duplicate check
        file_content = file.read()
        file.seek(0)  # Reset file pointer for later save
        
        # Check for duplicates (unless force_reprocess is enabled)
        force_reprocess = _parse_bool(request.form.get('force_reprocess'), default=False)
        
        if not force_reprocess:
            duplicate_check = _check_duplicate_upload(file_content, file.filename)
            
            if duplicate_check['is_duplicate']:
                existing = duplicate_check['existing_candidate']
                logger.info(f"Duplicate upload detected: {file.filename} -> {existing['anonymized_id']}")
                
                return jsonify({
                    'success': False,
                    'error': 'Duplicate CV detected',
                    'is_duplicate': True,
                    'existing_candidate': {
                        'anonymized_id': existing['anonymized_id'],
                        'uploaded_at': existing.get('created_at', 'Unknown')[:19],
                        'years_experience': existing.get('years_experience', 'N/A'),
                        'primary_domain': existing.get('primary_domain', 'N/A'),
                        'core_skills': existing.get('core_skills', [])
                    },
                    'message': f"This CV was already uploaded as {existing['anonymized_id']}. Use 'force_reprocess' to upload anyway."
                }), 409  # 409 Conflict
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)
        
        logger.info(f"File uploaded: {upload_path}")

        job_description = request.form.get('job_description', '').strip() or None
        effective_job_description = job_description or _DEFAULT_PROFILE_JD
        async_requested = _parse_bool(
            request.form.get('async', request.args.get('async')),
            default=_UPLOAD_ASYNC_DEFAULT
        )
        force_reprocess = _parse_bool(request.form.get('force_reprocess'), default=False)
        logger.info(
            "Upload request async=%s job_description_present=%s value_preview=%r",
            async_requested,
            bool(job_description),
            (job_description or '')[:80]
        )
        llm_runtime_config = _extract_runtime_llm_config({
            'llm_provider': request.form.get('llm_provider'),
            'llm_api_key': request.form.get('llm_api_key'),
            'llm_model': request.form.get('llm_model')
        })

        # Upload CV must use the user's own LLM API key. Do not fall back to server defaults.
        if not llm_runtime_config.get('api_key'):
            return jsonify({
                'success': False,
                'error': 'LLM API key is required for Upload CV. Provide it in the LLM API Key field.',
                'code': 'LLM_API_KEY_REQUIRED'
            }), 400

        if async_requested:
            job_id = _create_async_upload_job(
                upload_path=upload_path,
                original_filename=filename,
                job_description=effective_job_description,
                llm_runtime_config=llm_runtime_config,
                force_reprocess=force_reprocess
            )
            
            logger.info(f"Returning job {job_id} to client. Queue size: {_upload_job_queue.qsize()}")
            return jsonify({
                'success': True,
                'mode': 'asynchronous',
                'status': 'queued',
                'job_id': job_id,
                'status_url': url_for('get_upload_job_status', job_id=job_id),
                'message': 'Upload accepted. Poll status_url for completion.',
                'queue_size': _upload_job_queue.qsize()
            })

        # Optional synchronous mode: redact always and run intelligence extraction when JD is provided.
        try:
            pipeline_result = process_source_cv(
                cv_path=Path(upload_path),
                job_description=effective_job_description,
                force_reprocess=force_reprocess,
                llm_runtime_config=llm_runtime_config
            )

            # Safety fallback: if sync upload somehow returns redaction-only,
            # run extraction/persistence from the generated redacted text so
            # Supabase stays current for newly uploaded CVs.
            if pipeline_result.get('success') and not pipeline_result.get('intelligence'):
                try:
                    redacted_filename = pipeline_result.get('redacted_filename')
                    redacted_path = Path(app.config['OUTPUT_FOLDER']) / str(redacted_filename or '')
                    if redacted_filename and redacted_path.exists():
                        with open(redacted_path, 'r', encoding='utf-8') as redacted_file:
                            redacted_text = redacted_file.read()

                        fallback_result = process_redacted_cv_text(
                            redacted_text=redacted_text,
                            redacted_filename=redacted_filename,
                            job_description=job_description,
                            original_filename=filename,
                            force_reprocess=force_reprocess,
                            llm_runtime_config=llm_runtime_config
                        )

                        if fallback_result.get('success') and fallback_result.get('intelligence'):
                            fallback_result['preview'] = pipeline_result.get('preview', redacted_text)
                            pipeline_result = fallback_result
                except Exception as fallback_error:
                    logger.warning(f"Upload fallback extraction skipped: {fallback_error}")

            if not pipeline_result.get('success'):
                return jsonify({'error': pipeline_result.get('error', 'CV processing failed')}), 500

            # Invalidate search cache when new candidate is added
            try:
                from redis_cache import invalidate_search_cache
                deleted = invalidate_search_cache()
                if deleted > 0:
                    logger.info(f"✓ Invalidated {deleted} search cache entries after new candidate upload")
            except Exception as cache_err:
                logger.warning(f"Could not invalidate search cache: {cache_err}")

            response = _build_upload_success_payload(pipeline_result, mode='synchronous')

            logger.info(f"CV processed successfully: {pipeline_result['redacted_filename']}")
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error processing CV: {str(e)}", exc_info=True)
            return jsonify({'error': f'Error processing CV: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500


@app.route('/api/upload-jobs/<job_id>', methods=['GET'])
def get_upload_job_status(job_id):
    """Poll asynchronous upload job status and retrieve final result when completed."""
    try:
        # Try Supabase first
        storage = get_supabase_storage()
        job = None

        if storage:
            try:
                job = storage.get_upload_job(job_id)
                if job:
                    logger.debug(f"Job {job_id} found in Supabase: status={job.get('status')}")
            except Exception as e:
                logger.warning(f"Failed to get job from Supabase: {e}")

        # Fallback to memory
        if not job:
            with _upload_jobs_lock:
                _cleanup_upload_jobs_locked()
                job = _upload_jobs.get(job_id)
                if job:
                    logger.debug(f"Job {job_id} found in memory: status={job.get('status')}")

        if not job:
            logger.warning(f"Job not found: {job_id}")
            with _upload_jobs_lock:
                memory_jobs = list(_upload_jobs.keys())
            logger.warning(f"Available jobs in memory: {memory_jobs}")
            # Return 404 for correctness, but keep response JSON-shaped for UI.
            return jsonify({'success': False, 'mode': 'asynchronous', 'job_id': job_id, 'status': 'not_found', 'error': 'Job not found'}), 404

        status = job.get('status', 'queued')
        base_payload = {
            'success': status != 'failed',
            'mode': 'asynchronous',
            'job_id': job_id,
            'status': status,
            'submitted_at': job.get('submitted_at'),
            'started_at': job.get('started_at'),
            'completed_at': job.get('completed_at'),
            'job_description_provided': bool(job.get('job_description_provided')),
            'queue_size': _upload_job_queue.qsize()
        }

        if status == 'completed':
            pipeline_result = job.get('pipeline_result') or {}
            if isinstance(pipeline_result, str):
                try:
                    pipeline_result = json.loads(pipeline_result)
                except Exception:
                    pipeline_result = {'redacted_filename': None, 'error': 'pipeline_result_not_json'}

            final_payload = _build_upload_success_payload(pipeline_result, mode='asynchronous')
            final_payload.update(base_payload)
            return jsonify(final_payload)

        if status == 'failed':
            base_payload['error'] = job.get('error', 'Upload processing failed')
            # Return 200 so polling UI can handle job failure gracefully.
            return jsonify(base_payload)

        return jsonify(base_payload)

    except Exception as e:
        logger.error(f"Error retrieving upload job status for {job_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'mode': 'asynchronous', 'job_id': job_id, 'status': 'error', 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download the redacted CV"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='text/plain'
            )
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500


@app.route('/download/original/<anonymized_id>')
def download_original_cv(anonymized_id: str):
    """Download the original uploaded CV for a candidate by anonymized ID."""
    try:
        if not anonymized_id:
            return jsonify({'error': 'anonymized_id required'}), 400

        storage = get_supabase_storage()
        mapping = _get_filename_mapping(anonymized_id=anonymized_id, storage=storage)
        original_filename = (mapping or {}).get('original_filename')

        # Fallback to candidate record when mapping is missing
        if not original_filename and storage:
            raw_candidate = try_supabase_operation(
                lambda: storage.get_candidate(anonymized_id),
                fallback_result=None,
                timeout_seconds=10
            )
            if isinstance(raw_candidate, dict):
                original_filename = raw_candidate.get('original_filename')

        if not original_filename:
            fallback = _fallback_filenames_from_local_intelligence(anonymized_id)
            original_filename = fallback.get('original_filename')

        if not original_filename:
            return jsonify({'error': f'Original filename not found for {anonymized_id}'}), 404

        upload_path = _find_original_cv_anywhere(original_filename)

        # If we still can't find it by name, try archive path derived from Supabase ingest metadata.
        if (not upload_path or not upload_path.exists()) and storage:
            raw_candidate = try_supabase_operation(
                lambda: storage.get_candidate(anonymized_id),
                fallback_result=None,
                timeout_seconds=10
            )
            if isinstance(raw_candidate, dict):
                rel_path = _parse_archive_source_rel_path(raw_candidate.get('best_knowledge_summary'))
                if rel_path:
                    archive_root = _RUNTIME_DATA_ROOT / 'archive' / 'samples'
                    archive_candidate = _safe_join_under(archive_root, rel_path)
                    if archive_candidate and archive_candidate.exists():
                        upload_path = archive_candidate

        if not upload_path or not upload_path.exists():
            return jsonify({
                'error': f'Original CV file not found on server for {anonymized_id}',
                'anonymized_id': anonymized_id,
                'expected_original_filename': Path(original_filename).name,
                'hint': 'This server can only open originals that exist on disk. For archive-ingested candidates, ensure archive/samples is present on this machine; otherwise upload the CV again on this instance.'
            }), 404

        ext = upload_path.suffix.lower()
        guessed_mime, _ = mimetypes.guess_type(str(upload_path))
        mimetype = guessed_mime or 'application/octet-stream'
        if ext == '.pdf':
            mimetype = 'application/pdf'
        elif ext == '.docx':
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif ext == '.doc':
            mimetype = 'application/msword'

        # PDFs should open inline in the browser; user can still download from the viewer.
        if ext == '.pdf':
            response = send_file(
                str(upload_path),
                as_attachment=False,
                mimetype=mimetype
            )
            response.headers['Content-Disposition'] = f'inline; filename="{Path(original_filename).name}"'
            return response

        response = send_file(
            str(upload_path),
            as_attachment=True,
            download_name=Path(original_filename).name,
            mimetype=mimetype
        )
        return response

    except Exception as e:
        logger.error(f"Error downloading original CV for {anonymized_id}: {e}", exc_info=True)
        return jsonify({'error': f'Error downloading original CV: {str(e)}'}), 500


@app.route('/api/download-redacted-zip', methods=['POST'])
def download_redacted_zip():
    """Download a single ZIP containing redacted CVs for the provided anonymized IDs."""
    try:
        payload = request.get_json() or {}
        candidate_ids = payload.get('candidate_ids')
        if not isinstance(candidate_ids, list) or not candidate_ids:
            return jsonify({'error': 'candidate_ids (non-empty list) required'}), 400

        normalized_ids = []
        for raw in candidate_ids:
            if not raw:
                continue
            text = str(raw).strip()
            if text:
                normalized_ids.append(text)

        if not normalized_ids:
            return jsonify({'error': 'candidate_ids contained no valid IDs'}), 400

        storage = get_supabase_storage()
        output_dir = Path(app.config['OUTPUT_FOLDER'])

        # Batch pull candidate fields from Supabase (fast path for redacted text).
        supabase_candidates = _supabase_get_candidate_fields(storage, normalized_ids)
        supabase_originals = {k: v.get('original_filename') for k, v in supabase_candidates.items() if isinstance(v, dict)}

        missing: List[Dict[str, Any]] = []
        zip_items: List[Dict[str, Any]] = []
        redaction_errors: List[Dict[str, Any]] = []

        for anonymized_id in normalized_ids:
            # 1) Prefer an existing cached redaction named by anonymized_id.
            cached_by_id = output_dir / f"{anonymized_id}.txt"
            if cached_by_id.exists():
                zip_items.append({'anonymized_id': anonymized_id, 'mode': 'file', 'path': cached_by_id})
                continue

            # 1b) If Supabase has cleaned_text, use it directly (no local files needed).
            supa_row = supabase_candidates.get(anonymized_id) if isinstance(supabase_candidates, dict) else None
            supa_text = supa_row.get('cleaned_text') if isinstance(supa_row, dict) else None
            if isinstance(supa_text, str) and supa_text.strip():
                try:
                    with open(cached_by_id, 'w', encoding='utf-8') as f:
                        f.write(supa_text)
                    zip_items.append({'anonymized_id': anonymized_id, 'mode': 'file', 'path': cached_by_id})
                    continue
                except Exception as e:
                    redaction_errors.append({'anonymized_id': anonymized_id, 'reason': f'cache_write_failed:{e}'})

            # 2) Try mapping -> redacted filename (legacy).
            mapping = _get_filename_mapping(anonymized_id=anonymized_id, storage=storage)
            mapped_redacted = (mapping or {}).get('anonymized_filename')
            if mapped_redacted:
                mapped_redacted = Path(str(mapped_redacted)).name
                mapped_path = output_dir / mapped_redacted
                if mapped_path.exists():
                    zip_items.append({'anonymized_id': anonymized_id, 'mode': 'file', 'path': mapped_path})
                    continue

            # 3) Generate missing redaction from original CV (uploads/ or archive/samples/).
            original_filename = (mapping or {}).get('original_filename') or supabase_originals.get(anonymized_id)
            if not original_filename:
                fallback = _fallback_filenames_from_local_intelligence(anonymized_id)
                original_filename = fallback.get('original_filename')

            if not original_filename:
                missing.append({'anonymized_id': anonymized_id, 'reason': 'missing_original_filename'})
                zip_items.append({'anonymized_id': anonymized_id, 'mode': 'missing', 'reason': 'missing_original_filename'})
                continue

            original_path = _find_original_cv_anywhere(original_filename)

            # For archive-ingested candidates, prefer rel_path from Supabase metadata.
            if (not original_path or not original_path.exists()) and isinstance(supa_row, dict):
                rel_path = _parse_archive_source_rel_path(supa_row.get('best_knowledge_summary'))
                if rel_path:
                    archive_root = _RUNTIME_DATA_ROOT / 'archive' / 'samples'
                    archive_candidate = _safe_join_under(archive_root, rel_path)
                    if archive_candidate and archive_candidate.exists():
                        original_path = archive_candidate
            if not original_path or not original_path.exists():
                missing.append({'anonymized_id': anonymized_id, 'reason': 'original_file_missing_on_server'})
                zip_items.append({'anonymized_id': anonymized_id, 'mode': 'missing', 'reason': 'original_file_missing_on_server'})
                continue

            try:
                source_hash = _sha256_for_file(original_path)[:16]
                redaction_lock = _get_named_lock(_redaction_lock_registry, source_hash)
                with redaction_lock:
                    # Another request may have generated it while we waited.
                    if cached_by_id.exists():
                        zip_items.append({'anonymized_id': anonymized_id, 'mode': 'file', 'path': cached_by_id})
                        continue

                    redacted_text = _redact_cv_text_only(original_path)
                    if not redacted_text:
                        raise ValueError('empty_redacted_text')
                    # Cache as anonymized_id-named file for deterministic bulk downloads.
                    with open(cached_by_id, 'w', encoding='utf-8') as f:
                        f.write(redacted_text)

                zip_items.append({'anonymized_id': anonymized_id, 'mode': 'file', 'path': cached_by_id})
            except Exception as e:
                redaction_errors.append({'anonymized_id': anonymized_id, 'reason': f'redaction_failed:{e}'})
                zip_items.append({'anonymized_id': anonymized_id, 'mode': 'missing', 'reason': f'redaction_failed:{e}'})

        if not zip_items:
            return jsonify({
                'error': 'No redacted CVs could be generated or resolved for download',
                'missing': missing,
                'redaction_errors': redaction_errors
            }), 404

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for item in zip_items:
                anonymized_id = item['anonymized_id']
                arcname = f"{anonymized_id}.txt"
                if item.get('mode') == 'file':
                    path = item.get('path')
                    zipf.write(str(path), arcname=arcname)
                else:
                    reason = item.get('reason') or 'missing'
                    zipf.writestr(arcname, f"[MISSING REDACTED CV]\nCandidate: {anonymized_id}\nReason: {reason}\n")

            missing_all = []
            missing_all.extend(missing)
            missing_all.extend(redaction_errors)
            if missing_all:
                missing_lines = [
                    'Some candidates could not be included in this ZIP:',
                    ''
                ]
                for item in missing_all:
                    missing_lines.append(f"- {item.get('anonymized_id')}: {item.get('reason')}")
                zipf.writestr('MISSING.txt', "\n".join(missing_lines) + "\n")

        zip_buffer.seek(0)
        download_name = 'recommended_redacted_cvs.zip'
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )

    except Exception as e:
        logger.error(f"Error creating redacted ZIP: {e}", exc_info=True)
        return jsonify({'error': f'Error creating ZIP: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint with connection status"""
    supabase_probe = probe_supabase_runtime()
    if supabase_probe['reachable']:
        supabase_status = 'connected'
    elif supabase_probe['configured']:
        supabase_status = 'configured but unreachable (using local fallback)'
    else:
        supabase_status = 'not configured'
    
    llm_probe = probe_llm_provider()
    embedding_probe = probe_embedding_runtime()
    
    # Count local data
    redacted_count = len(list(Path(app.config['OUTPUT_FOLDER']).glob('REDACTED_*.txt')))
    intelligence_count = len(list(Path(app.config['INTELLIGENCE_FOLDER']).glob('*_intelligence.json')))
    
    return jsonify({
        'status': 'healthy',
        'service': 'CV Redaction Pipeline',
        'supabase': supabase_status,
        'llm_provider': llm_probe['provider'],
        'llm_reachable': llm_probe['reachable'],
        'embedding_provider': embedding_probe['provider'],
        'embedding_reachable': embedding_probe['reachable'],
        'redacted_cvs': redacted_count,
        'intelligence_files': intelligence_count,
        'async_upload': {
            'default_async': _UPLOAD_ASYNC_DEFAULT,
            'worker_count': _UPLOAD_WORKER_COUNT,
            'queue_size': _upload_job_queue.qsize(),
            'jobs_tracked': len(_upload_jobs)
        },
        'llm_throttle': {
            'max_concurrent_requests': _LLM_MAX_CONCURRENT,
            'min_interval_seconds': _LLM_MIN_INTERVAL_SECONDS
        },
        'api_key_configured': llm_probe['configured'],
        'live_checks': {
            'llm': llm_probe,
            'supabase': supabase_probe,
            'embeddings': embedding_probe
        }
    })


@app.route('/api/triage/test', methods=['POST'])
def test_triage():
    """Test triage engine with CV and JD"""
    try:
        from enhanced_triage import get_triage_engine
        
        data = request.get_json()
        cv_text = data.get('cv_text')
        job_description = data.get('job_description')
        
        if not cv_text or not job_description:
            return jsonify({'error': 'Both cv_text and job_description required'}), 400
        
        triage_engine = get_triage_engine()
        should_process, reason, relevance_score = triage_engine.should_process(
            cv_text, job_description
        )
        
        # Extract keywords for debugging
        cv_keywords = triage_engine.extract_keywords(cv_text)
        jd_keywords = triage_engine.extract_keywords(job_description)
        intersection = cv_keywords.intersection(jd_keywords)
        
        priority = triage_engine.get_priority_from_score(relevance_score)
        
        return jsonify({
            'success': True,
            'should_process': should_process,
            'reason': reason,
            'relevance_score': relevance_score,
            'relevance_percent': f"{relevance_score * 100:.1f}%",
            'priority': priority,
            'priority_label': {0: 'HIGH', 5: 'NORMAL', 10: 'LOW'}.get(priority, 'UNKNOWN'),
            'cv_keywords_count': len(cv_keywords),
            'jd_keywords_count': len(jd_keywords),
            'matched_keywords_count': len(intersection),
            'matched_keywords': sorted(list(intersection))[:20],  # Show first 20
            'thresholds': {
                'extreme_mismatch': triage_engine.extreme_threshold,
                'poor_match': triage_engine.poor_threshold,
                'moderate_match': triage_engine.moderate_threshold
            }
        })
    except Exception as e:
        logger.error(f"Error testing triage: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/semantic', methods=['POST'])
def semantic_search():
    """Perform semantic search using vector embeddings"""
    try:
        data = request.get_json()
        query_text = data.get('query_text')
        
        if not query_text:
            return jsonify({'error': 'query_text required'}), 400
        
        limit = data.get('limit', 10)
        threshold = data.get('similarity_threshold', 0.7)
        filters = data.get('filters', {})
        
        # Try Supabase first
        storage = get_supabase_storage()
        if storage:
            results = try_supabase_operation(
                lambda: storage.semantic_search(
                    query_text=query_text,
                    limit=limit,
                    similarity_threshold=threshold,
                    filters=filters
                ),
                fallback_result=[],
                timeout_seconds=30
            )
            
            if results:
                return jsonify({
                    'success': True,
                    'query': query_text,
                    'count': len(results),
                    'results': results,
                    'data_source': 'supabase_vector'
                })
        
        # Local fallback - load embeddings from JSON files
        try:
            from vector_search import get_vector_search_engine
            
            engine = get_vector_search_engine()
            query_embedding = engine.generate_embedding(query_text)
            
            # Load local intelligence files with embeddings
            intelligence_dir = Path(app.config['INTELLIGENCE_FOLDER'])
            candidate_embeddings = []
            
            for json_file in intelligence_dir.glob('*_intelligence.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    embedding = data.get('embedding')
                    if embedding:
                        candidate_embeddings.append((
                            data.get('anonymized_id'),
                            embedding
                        ))
                except Exception:
                    continue
            
            # Search locally
            results = engine.search_local(
                query_embedding,
                candidate_embeddings,
                limit=limit,
                threshold=threshold
            )
            
            # Load full candidate data
            full_results = []
            for result in results:
                candidates = load_local_intelligence_files()
                candidate = next((c for c in candidates if c.get('anonymized_id') == result['candidate_id']), None)
                if candidate:
                    candidate['similarity_score'] = result['similarity_score']
                    full_results.append(candidate)
            
            return jsonify({
                'success': True,
                'query': query_text,
                'count': len(full_results),
                'results': full_results,
                'data_source': 'local_vector'
            })
            
        except Exception as e:
            logger.error(f"Local semantic search failed: {e}")
            return jsonify({'error': f'Semantic search not available: {str(e)}'}), 503
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/hybrid', methods=['POST'])
def hybrid_search():
    """Perform hybrid search (semantic + SQL filters)"""
    try:
        data = request.get_json()
        query_text = data.get('query_text')
        
        if not query_text:
            return jsonify({'error': 'query_text required'}), 400
        
        limit = data.get('limit', 10)
        filters = data.get('filters', {})
        semantic_weight = data.get('semantic_weight', 0.7)
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available for hybrid search'}), 503
        
        results = try_supabase_operation(
            lambda: storage.hybrid_search(
                query_text=query_text,
                filters=filters,
                limit=limit,
                semantic_weight=semantic_weight
            ),
            fallback_result=[],
            timeout_seconds=30
        )
        
        return jsonify({
            'success': True,
            'query': query_text,
            'count': len(results),
            'results': results,
            'semantic_weight': semantic_weight,
            'data_source': 'supabase_hybrid'
        })
        
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/redacted-files')
def list_redacted_files():
    """List all available redacted CV files"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        files = []
        for f in sorted(output_dir.glob('REDACTED_*.txt'), key=lambda x: x.stat().st_mtime, reverse=True):
            files.append({
                'filename': f.name,
                'size_bytes': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                'download_url': url_for('download_file', filename=f.name)
            })
        
        return jsonify({
            'success': True,
            'count': len(files),
            'files': files
        })
    except Exception as e:
        logger.error(f"Error listing redacted files: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Render the recruiter dashboard"""
    return render_template('dashboard.html')

@app.route('/api/extract-intelligence', methods=['POST'])
def extract_intelligence():
    """Extract intelligence from redacted CV with job description.
    Only processes anonymized CVs - returns error if CV is not anonymized.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        redacted_cv_file = data.get('redacted_cv_file')
        job_description = data.get('job_description')
        llm_runtime_config = _extract_runtime_llm_config(data)
        
        if not redacted_cv_file or not job_description:
            return jsonify({'error': 'Both redacted_cv_file and job_description required'}), 400
        
        # Read redacted CV
        cv_path = os.path.join(app.config['OUTPUT_FOLDER'], redacted_cv_file)
        if not os.path.exists(cv_path):
            return jsonify({'error': 'Redacted CV file not found'}), 404
        
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
        
        # Verify CV is anonymized before processing
        from cv_intelligence_extractor import is_cv_anonymized
        if not is_cv_anonymized(cv_text):
            return jsonify({
                'error': 'CV is not anonymized. Please redact PII first using the upload/redact feature before extracting intelligence.',
                'action_required': 'anonymize_first'
            }), 400
        
        result = process_redacted_cv_text(
            redacted_text=cv_text,
            redacted_filename=redacted_cv_file,
            job_description=job_description,
            original_filename=redacted_cv_file,
            force_reprocess=True,
            llm_runtime_config=llm_runtime_config
        )

        if not result.get('success'):
            return jsonify({
                'error': result.get('error', 'Intelligence extraction failed'),
                'action_required': 'anonymize_first'
            }), 400
        
        return jsonify({
            'success': True,
            'intelligence': result.get('intelligence'),
            'intelligence_file': result.get('intelligence_file'),
            'stored_in_supabase': result.get('stored_in_supabase', False),
            'stored_embedding_in_supabase': result.get('stored_embedding_in_supabase', False),
            'embedding_generated': result.get('embedding_generated', False),
            'similarity_score': result.get('similarity_score')
        })
        
    except Exception as e:
        logger.error(f"Error extracting intelligence: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-samples', methods=['POST'])
def process_samples():
    """
    Full pipeline for the sample corpus:
    original CV -> redaction -> LLM intelligence -> faithfulness -> embedding -> storage.
    """
    try:
        data = request.get_json() or {}
        job_description = (data.get('job_description') or '').strip() or None
        force_reprocess = data.get('force_reprocess', False)
        llm_runtime_config = _extract_runtime_llm_config(data)
        
        # Collect all original CVs from samples/ and samples/more/
        sample_dirs = [Path('samples'), Path('samples/more')]
        allowed_ext = {'.pdf', '.docx', '.doc'}
        original_cvs = []
        for sample_dir in sample_dirs:
            if sample_dir.exists():
                for f in sorted(sample_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in allowed_ext:
                        original_cvs.append(f)
        
        if not original_cvs:
            return jsonify({'error': 'No original CVs found in samples/ directory'}), 404
        
        logger.info(f"Processing {len(original_cvs)} original CVs through the full pipeline")
        
        results = []
        redacted_count = 0
        intelligence_count = 0
        embedding_count = 0
        stored_supabase_count = 0
        quota_exhausted = False
        
        for cv_path in original_cvs:
            cv_name = cv_path.name
            
            if quota_exhausted:
                results.append({
                    'file': cv_name, 'status': 'skipped',
                    'error': 'Skipped - API quota exhausted. Re-run later to continue.'
                })
                continue
            
            try:
                safe_name = secure_filename(cv_name)
                existing_redacted = list(Path(app.config['OUTPUT_FOLDER']).glob(f'REDACTED_*_{safe_name}*'))
                pipeline_result = process_source_cv(
                    cv_path=cv_path,
                    job_description=job_description,
                    force_reprocess=force_reprocess,
                    existing_redacted_path=existing_redacted[0] if (existing_redacted and not force_reprocess) else None,
                    llm_runtime_config=llm_runtime_config
                )

                if not existing_redacted or force_reprocess:
                    redacted_count += 1

                if pipeline_result.get('success'):
                    intelligence = pipeline_result.get('intelligence', {})
                    if pipeline_result.get('intelligence'):
                        intelligence_count += 1
                    if pipeline_result.get('embedding_generated'):
                        embedding_count += 1
                    if pipeline_result.get('stored_in_supabase'):
                        stored_supabase_count += 1

                    results.append({
                        'file': cv_name,
                        'status': 'success',
                        'cached': pipeline_result.get('cached', False),
                        'redacted_filename': pipeline_result.get('redacted_filename'),
                        'embedding_generated': pipeline_result.get('embedding_generated', False),
                        'stored_in_supabase': pipeline_result.get('stored_in_supabase', False),
                        'similarity_score': pipeline_result.get('similarity_score'),
                        'intelligence': {
                            'anonymized_id': intelligence.get('anonymized_id'),
                            'verdict': intelligence.get('verdict'),
                            'confidence_score': intelligence.get('confidence_score'),
                            'match_score': intelligence.get('match_score'),
                            'years_experience': intelligence.get('years_experience'),
                            'seniority_level': intelligence.get('seniority_level'),
                            'core_technical_skills': intelligence.get('core_technical_skills', []),
                            'primary_domain': intelligence.get('primary_domain', ''),
                            'verdict_reason': intelligence.get('verdict_reason', '')
                        }
                    })
                else:
                    results.append({
                        'file': cv_name,
                        'status': 'error',
                        'error': pipeline_result.get('error', 'Processing failed')
                    })
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing {cv_name}: {error_msg}")
                
                if 'quota' in error_msg.lower() or 'rate limit exceeded' in error_msg.lower() or '429' in error_msg:
                    quota_exhausted = True
                
                results.append({'file': cv_name, 'status': 'error', 'error': error_msg})
        
        successful = len([r for r in results if r.get('status') == 'success'])
        skipped = len([r for r in results if r.get('status') == 'skipped'])
        
        return jsonify({
            'success': True,
            'total_originals': len(original_cvs),
            'redacted': redacted_count,
            'intelligence_extracted': intelligence_count,
            'embeddings_generated': embedding_count,
            'stored_in_supabase': stored_supabase_count,
            'successful': successful,
            'failed': len(original_cvs) - successful - skipped,
            'skipped': skipped,
            'quota_exhausted': quota_exhausted,
            'triage_rejected': 0,
            'api_savings_percent': 0,
            'triage_enabled': False,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error processing samples: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch-extract', methods=['POST'])
def batch_extract_intelligence():
    """Batch extract intelligence from all redacted CVs.
    Only processes anonymized CVs — skips any that aren't properly redacted.
    """
    try:
        data = request.get_json() or {}
        job_description = (data.get('job_description') or '').strip() or None
        force_reprocess = data.get('force_reprocess', False)
        llm_runtime_config = _extract_runtime_llm_config(data)
        
        # Get all redacted CV files
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        cv_files = list(output_dir.glob('REDACTED_*.txt'))
        
        if not cv_files:
            return jsonify({'error': 'No redacted CVs found. Process sample CVs first.'}), 404
        
        from llm_batch_processor import QuotaExhaustedException
        
        results = []
        skipped_not_anonymized = 0
        quota_exhausted = False
        
        for cv_file in cv_files:
            # If quota exhausted, skip remaining immediately
            if quota_exhausted:
                results.append({
                    'file': cv_file.name,
                    'status': 'skipped',
                    'error': 'Skipped — API quota exhausted'
                })
                continue
            try:
                # Check if intelligence already exists (skip unless force_reprocess)
                intelligence_file = f"{cv_file.stem}_intelligence.json"
                intelligence_path = os.path.join(app.config['INTELLIGENCE_FOLDER'], intelligence_file)
                
                if os.path.exists(intelligence_path) and not force_reprocess:
                    try:
                        with open(intelligence_path, 'r', encoding='utf-8') as f:
                            intelligence = json.load(f)
                        if _is_cached_result_compatible(intelligence, job_description):
                            results.append({
                                'file': cv_file.name,
                                'status': 'success' if 'error' not in intelligence else 'error',
                                'intelligence': intelligence,
                                'cached': True
                            })
                            continue
                    except:
                        pass # If invalid JSON, re-process

                with open(cv_file, 'r', encoding='utf-8') as f:
                    cv_text = f.read()

                result = process_redacted_cv_text(
                    redacted_text=cv_text,
                    redacted_filename=cv_file.name,
                    job_description=job_description,
                    original_filename=cv_file.name,
                    force_reprocess=force_reprocess,
                    llm_runtime_config=llm_runtime_config
                )

                if not result.get('success') and 'anonymized' in (result.get('error', '').lower()):
                    skipped_not_anonymized += 1

                results.append({
                    'file': cv_file.name,
                    'status': 'success' if result.get('success') else 'error',
                    'cached': result.get('cached', False),
                    'embedding_generated': result.get('embedding_generated', False),
                    'stored_in_supabase': result.get('stored_in_supabase', False),
                    'intelligence': result.get('intelligence'),
                    'error': result.get('error')
                })
                
            except QuotaExhaustedException as qe:
                logger.error(f"Quota exhausted during batch extract: {qe}")
                quota_exhausted = True
                results.append({
                    'file': cv_file.name,
                    'status': 'error',
                    'error': str(qe)
                })
                continue
            except Exception as e:
                logger.error(f"Error processing {cv_file}: {e}")
                results.append({
                    'file': cv_file.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        successful = len([r for r in results if r.get('status') == 'success'])
        skipped = len([r for r in results if r.get('status') == 'skipped'])
        embeddings_generated = len([r for r in results if r.get('embedding_generated')])
        stored_in_supabase = len([r for r in results if r.get('stored_in_supabase')])
        
        response_data = {
            'success': True,
            'total': len(cv_files),
            'successful': successful,
            'failed': len(cv_files) - successful - skipped,
            'skipped': skipped,
            'embeddings_generated': embeddings_generated,
            'stored_in_supabase': stored_in_supabase,
            'quota_exhausted': quota_exhausted,
            'results': results
        }
        if skipped_not_anonymized > 0:
            response_data['skipped_not_anonymized'] = skipped_not_anonymized
            response_data['message'] = f'{skipped_not_anonymized} CVs were skipped because they are not anonymized. Please redact PII first.'
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        with open("last_error.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {str(e)}\n\nTraceback:\n")
            traceback.print_exc(file=f)
        logger.error(f"Error in batch extraction: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-candidates', methods=['POST'])
def search_candidates():
    """Search candidates using filters from Supabase only."""
    try:
        data = request.get_json() or {}
        limit_raw = data.get('limit', 5000)
        try:
            limit = int(limit_raw) if limit_raw is not None else 5000
        except Exception:
            limit = 5000
        if limit <= 0:
            limit = 5000
        
        storage = get_supabase_storage()
        if not storage:
            cached_candidates = _get_quick_search_cache_snapshot()
            if cached_candidates:
                filtered = _filter_candidate_records(cached_candidates, data)[:limit]
                return jsonify({
                    'success': True,
                    'count': len(filtered),
                    'candidates': filtered,
                    'data_source': 'supabase_cache_stale',
                    'supabase_only': True
                })
            return jsonify({
                'success': False,
                'error': 'Supabase is not reachable. Supabase-only mode is enabled.',
                'data_source': 'supabase',
                'supabase_only': True
            }), 503

        raw_results = try_supabase_operation(
            lambda: storage.search_by_filters(
                verdict=data.get('verdict'),
                seniority_level=data.get('seniority_level'),
                min_match_score=data.get('min_match_score'),
                min_confidence_score=data.get('min_confidence_score'),
                required_skills=data.get('required_skills'),
                domains=data.get('domains'),
                primary_domain=data.get('primary_domain'),
                min_years_experience=data.get('min_years_experience'),
                max_years_experience=data.get('max_years_experience'),
                limit=limit
            ),
            fallback_result=None,
            timeout_seconds=10
        )
        if raw_results is None:
            candidate_payload = _get_quick_search_candidates(storage=storage, limit=5000)
            cached_rows = candidate_payload.get('candidates', [])
            if not cached_rows:
                return jsonify({
                    'success': False,
                    'error': 'Supabase query failed or timed out. Supabase-only mode is enabled.',
                    'data_source': 'supabase',
                    'supabase_only': True
                }), 503

            filtered_cached = _filter_candidate_records(cached_rows, data)[:limit]
            return jsonify({
                'success': True,
                'count': len(filtered_cached),
                'candidates': filtered_cached,
                'data_source': candidate_payload.get('source', 'supabase_cache_stale'),
                'cache_age_seconds': candidate_payload.get('cache_age_seconds'),
                'supabase_only': True
            })

        results = [
            candidate
            for candidate in (storage._db_record_to_app_format(r) for r in raw_results)
            if _candidate_has_searchable_signal(candidate)
        ]
        return jsonify({
            'success': True,
            'count': len(results),
            'candidates': results,
            'data_source': 'supabase_live',
            'supabase_only': True
        })
        
    except Exception as e:
        logger.error(f"Error searching candidates: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/quick-search', methods=['POST'])
def quick_search_api():
    """Quick JD-to-candidate search using PURE SEMANTIC ranking (NO keyword matching)."""
    try:
        import time
        from vector_search import get_vector_search_engine
        from redis_cache import (
            get_search_results_from_cache,
            cache_search_results,
            REDIS_AVAILABLE
        )
        
        data = request.get_json() or {}
        job_description = data.get('job_description', '')
        requested_limit = data.get('limit', 15)
        
        try:
            requested_limit = int(requested_limit)
        except Exception:
            requested_limit = 15

        # If limit is <= 0, treat it as "return all matches".
        # Otherwise, honor the requested limit without an artificial cap.
        limit = None
        cache_limit_key = 0
        if requested_limit and requested_limit > 0:
            limit = requested_limit
            cache_limit_key = requested_limit
        
        if not job_description:
            return jsonify({'error': 'job_description required'}), 400
        
        # Check Redis cache for search results
        if REDIS_AVAILABLE:
            cached_results = get_search_results_from_cache(job_description, cache_limit_key)
            if cached_results is not None:
                logger.info(f"✓ Returning cached search results ({cached_results.get('total_matches', 0)} matches)")
                cached_results['cache_hit'] = True
                return jsonify(cached_results)
        
        start_time = time.time()
        data_source = 'supabase'
        candidate_rows = []
        cache_age_seconds = None

        # ALWAYS use semantic ranking (NO keyword fallback)
        try:
            engine = get_vector_search_engine()
            jd_embedding = engine.generate_embedding(job_description)
            logger.info(f"Generated JD embedding for semantic search ({len(jd_embedding)} dimensions)")
        except Exception as e:
            logger.error(f"Could not generate JD embedding: {e}")
            return jsonify({
                'success': False,
                'error': f'Semantic ranking failed: {str(e)}. Please ensure embedding model is available.'
            }), 500

        storage = get_supabase_storage()
        if storage:
            candidate_payload = _get_quick_search_candidates(storage=storage, limit=5000)
            candidate_rows = candidate_payload.get('candidates', [])
            data_source = candidate_payload.get('source', 'supabase')
            cache_age_seconds = candidate_payload.get('cache_age_seconds')
        else:
            candidate_rows = _get_quick_search_cache_snapshot()
            if candidate_rows:
                data_source = 'supabase_cache_stale'
            else:
                return jsonify({
                    'success': False,
                    'error': 'Supabase is not reachable and no cached candidates are available.',
                    'data_source': 'supabase',
                    'supabase_only': True
                }), 503

        matches = []
        
        # PURE SEMANTIC RANKING - NO KEYWORD MATCHING
        for intel in candidate_rows:
            if 'error' in intel and not intel.get('verdict'):
                continue
            if not _candidate_has_searchable_signal(intel):
                continue
            
            # Use ONLY semantic ranking (contextual understanding)
            ranked = compute_semantic_candidate_match(
                candidate=intel,
                jd_embedding=jd_embedding,
                job_description=job_description
            )

            match_percentage = ranked['match_percentage']
            matched_keywords = ranked.get('matched_keywords', [])
            reason = ranked['reason']
            critical_coverage_raw = ranked.get('critical_skill_coverage')
            critical_coverage = (
                float(critical_coverage_raw)
                if isinstance(critical_coverage_raw, (int, float))
                else None
            )
            min_required_coverage = float(ranked.get('critical_skill_min_required') or 0.0)
            critical_required = ranked.get('critical_skills_required') or []
            semantic_score = ranked.get('semantic_score', 0)
            
            match_data = {
                'anonymized_id': intel.get('anonymized_id', 'UNKNOWN'),
                'match_percentage': match_percentage,
                'semantic_score': semantic_score,
                'matched_keywords': matched_keywords,
                'selection_basis': ranked.get('selection_basis', ''),
                'critical_skills_required': critical_required,
                'critical_skills_matched': ranked.get('critical_skills_matched', []),
                'critical_skills_missing': ranked.get('critical_skills_missing', []),
                'best_knowledge': ranked.get('best_knowledge') or intel.get('best_knowledge_summary', ''),
                'verdict': intel.get('verdict'),
                'confidence_score': intel.get('confidence_score', 0),
                'years_experience': intel.get('years_experience', 0),
                'seniority_level': intel.get('seniority_level', 'N/A'),
                'core_technical_skills': intel.get('core_technical_skills', [])[:5],
                'primary_domain': intel.get('primary_domain', ''),
                'verdict_reason': intel.get('verdict_reason', ''),
                'match_reason': reason
            }

            if critical_coverage is not None:
                match_data['critical_skill_coverage'] = critical_coverage
            
            matches.append(match_data)
        
        # Deduplicate and sort by semantic similarity
        deduped_matches = {}
        for match in matches:
            key = match['anonymized_id']
            current = deduped_matches.get(key)
            if current is None or match['semantic_score'] > current['semantic_score']:
                deduped_matches[key] = match

        matches = list(deduped_matches.values())
        matches.sort(
            key=lambda x: (
                x['semantic_score'],  # Primary: semantic similarity
                x.get('confidence_score', 0),
                x.get('years_experience', 0)
            ),
            reverse=True
        )
        top_matches = matches if limit is None else matches[:limit]
        
        elapsed = time.time() - start_time
        
        result = {
            'success': True,
            'matches': top_matches,
            'total_candidates_searched': len(candidate_rows),
            'total_matches': len(matches),
            'search_time': f'{elapsed:.3f}s',
            'data_source': data_source,
            'cache_age_seconds': cache_age_seconds,
            'supabase_only': True,
            'ranking_method': 'pure_semantic_similarity',
            'embedding_model': engine.embedding_provider,
            'embedding_dimensions': engine.dimensions,
            'cache_hit': False
        }
        
        # Cache the search results in Redis (5 minute TTL)
        if REDIS_AVAILABLE:
            cache_search_results(job_description, cache_limit_key, result, ttl_seconds=300)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in quick search: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidate/<anonymized_id>')
def get_candidate(anonymized_id):
    """Get specific candidate details by anonymized ID - with local fallback"""
    try:
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            raw_candidate = try_supabase_operation(
                lambda: storage.get_candidate(anonymized_id),
                fallback_result=None,
                timeout_seconds=10
            )
            if raw_candidate:
                candidate = storage._db_record_to_app_format(raw_candidate)
                return jsonify({
                    'success': True,
                    'candidate': candidate,
                    'data_source': 'supabase'
                })
        
        # Local fallback - search JSON files
        candidates = load_local_intelligence_files()
        candidate = next((c for c in candidates if c.get('anonymized_id') == anonymized_id), None)
        
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        return jsonify({
            'success': True,
            'candidate': candidate,
            'data_source': 'local_json'
        })
        
    except Exception as e:
        logger.error(f"Error getting candidate: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get database statistics - with local fallback"""
    try:
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            result = try_supabase_operation(
                lambda: storage.get_statistics(),
                fallback_result=None,
                timeout_seconds=10
            )
            if result:
                result['data_source'] = 'supabase'
                return jsonify({'success': True, 'statistics': result})
        
        # Local fallback
        stats = get_local_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-candidates')
def get_all_candidates():
    """Get all candidates with pagination - with local fallback"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            raw_candidates = try_supabase_operation(
                lambda: storage.get_all_candidates(limit=limit),
                fallback_result=None,
                timeout_seconds=10
            )
            if raw_candidates is not None:
                # Convert DB records to app format
                candidates = [
                    candidate
                    for candidate in (storage._db_record_to_app_format(r) for r in raw_candidates)
                    if _candidate_has_searchable_signal(candidate)
                ]
                return jsonify({
                    'success': True,
                    'count': len(candidates),
                    'candidates': candidates,
                    'data_source': 'supabase'
                })
        
        # Local fallback
        candidates = [c for c in load_local_intelligence_files() if _candidate_has_searchable_signal(c)][:limit]
        return jsonify({
            'success': True,
            'count': len(candidates),
            'candidates': candidates,
            'data_source': 'local_json'
        })
        
    except Exception as e:
        logger.error(f"Error getting all candidates: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/review-queue')
def get_review_queue():
    """Get candidates requiring human review (confidence < 70%) - with local fallback"""
    try:
        return jsonify({
            'success': True,
            'count': 0,
            'candidates': [],
            'message': 'Human review queue is disabled for now.',
            'data_source': 'disabled'
        })
        
    except Exception as e:
        logger.error(f"Error getting review queue: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/recruiter-override/<anonymized_id>', methods=['POST'])
def add_recruiter_override(anonymized_id):
    """Add recruiter's final decision to candidate - with local fallback"""
    try:
        data = request.get_json()
        
        if not data or 'decision' not in data:
            return jsonify({'error': 'decision field required (SHORTLIST/REJECT/HIRED)'}), 400
        
        recruiter_decision = data.get('decision')
        recruiter_notes = data.get('notes', '')
        recruiter_id = data.get('recruiter_id', 'recruiter')
        
        # Validate decision
        valid_decisions = ['SHORTLIST', 'REJECT', 'HIRED', 'ON_HOLD']
        if recruiter_decision not in valid_decisions:
            return jsonify({'error': f'Invalid decision. Must be one of: {valid_decisions}'}), 400
        
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            result = try_supabase_operation(
                lambda: storage.add_recruiter_override(
                    anonymized_id,
                    recruiter_decision,
                    recruiter_notes,
                    recruiter_id
                ),
                fallback_result=None,
                timeout_seconds=5
            )
            if result:
                return jsonify({
                    'success': True,
                    'message': f'Recruiter override added: {recruiter_decision}',
                    'candidate': result,
                    'data_source': 'supabase'
                })
        
        # Local fallback - update the JSON file
        intelligence_dir = Path(app.config['INTELLIGENCE_FOLDER'])
        updated = False
        for json_file in intelligence_dir.glob('*_intelligence.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                if file_data.get('anonymized_id') == anonymized_id:
                    file_data['recruiter_override'] = recruiter_decision
                    file_data['recruiter_notes'] = recruiter_notes
                    file_data['recruiter_id'] = recruiter_id
                    file_data['reviewed_at'] = datetime.now().isoformat()
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(file_data, f, indent=2, ensure_ascii=False)
                    updated = True
                    break
            except Exception:
                continue
        
        if updated:
            return jsonify({
                'success': True,
                'message': f'Recruiter override saved locally: {recruiter_decision}',
                'data_source': 'local_json'
            })
        else:
            return jsonify({'error': 'Candidate not found'}), 404
        
    except Exception as e:
        logger.error(f"Error adding recruiter override: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync-to-supabase', methods=['POST'])
def sync_to_supabase():
    """Sync all local intelligence JSON files to Supabase database"""
    try:
        if not is_supabase_configured():
            return jsonify({'error': 'Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env'}), 503
        
        # Reset the reachability flag to retry
        global _supabase_reachable, _supabase_storage
        _supabase_reachable = None
        _supabase_storage = None
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Cannot connect to Supabase. Is the project active?'}), 503
        
        candidates = load_local_intelligence_files()
        
        if not candidates:
            return jsonify({'error': 'No local intelligence files to sync'}), 404
        
        synced = 0
        errors = 0
        
        for candidate in candidates:
            try:
                # Load the full JSON file for this candidate
                filename = candidate.get('_filename', '')
                filepath = Path(app.config['INTELLIGENCE_FOLDER']) / filename
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        full_data = json.load(f)
                    
                    result = try_supabase_operation(
                        lambda d=full_data: storage.store_intelligence(d),
                        fallback_result=None,
                        timeout_seconds=10
                    )
                    if result is not None:
                        synced += 1
                    else:
                        errors += 1
            except Exception as e:
                logger.warning(f"Sync error for {candidate.get('anonymized_id')}: {e}")
                errors += 1
        
        return jsonify({
            'success': True,
            'total': len(candidates),
            'synced': synced,
            'errors': errors,
            'message': f'Synced {synced}/{len(candidates)} records to Supabase'
        })
        
    except Exception as e:
        logger.error(f"Error syncing to Supabase: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-status')
def connection_status():
    """Check real-time connection status of all services"""
    llm_probe = probe_llm_provider()
    embedding_probe = probe_embedding_runtime()
    supabase_probe = probe_supabase_runtime()
    status = {
        'supabase': {
            'configured': supabase_probe['configured'],
            'reachable': supabase_probe['reachable'],
            'url': os.getenv('SUPABASE_URL', 'NOT SET'),
            'message': supabase_probe['message']
        },
        'llm': {
            **llm_probe,
            'api_key_set': llm_probe['configured']
        },
        'embeddings': {
            **embedding_probe
        },
        'local_data': {
            'redacted_cvs': len(list(Path(app.config['OUTPUT_FOLDER']).glob('REDACTED_*.txt'))),
            'intelligence_files': len(list(Path(app.config['INTELLIGENCE_FOLDER']).glob('*_intelligence.json')))
        },
        'env_loaded_from': '.env file' if os.path.exists('.env') else 'system environment'
    }
    return jsonify(status)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("CV Redaction Pipeline - Web Interface")
    print("="*60)
    print(f"\nServer starting...")
    print(f"Upload folder: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    print(f"Output folder: {os.path.abspath(app.config['OUTPUT_FOLDER'])}")
    print(f"\nAccess the application at: http://localhost:5000")
    print(f"Press CTRL+C to stop the server\n")
    
    # Threaded mode improves local concurrency behavior during load tests.
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
