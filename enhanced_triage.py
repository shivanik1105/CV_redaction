"""
Enhanced Triage Engine - "The Bouncer"
Auto-reject irrelevant CVs before expensive LLM calls using set intersection
"""
import re
import logging
from typing import Tuple, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedTriageEngine:
    """
    Enhanced triage engine using set intersection for CV relevance scoring.
    Implements multi-tier rejection thresholds to filter out irrelevant CVs
    before making expensive LLM API calls.
    """
    
    # Stopwords to exclude from keyword extraction
    STOPWORDS = {
        'about', 'above', 'after', 'again', 'against', 'all', 'also', 'am', 'an', 'and',
        'any', 'are', 'aren', 'as', 'at', 'be', 'because', 'been', 'before', 'being',
        'below', 'between', 'both', 'but', 'by', 'can', 'cannot', 'could', 'couldn',
        'did', 'didn', 'do', 'does', 'doesn', 'doing', 'don', 'down', 'during', 'each',
        'few', 'for', 'from', 'further', 'had', 'hadn', 'has', 'hasn', 'have', 'haven',
        'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how',
        'i', 'if', 'in', 'into', 'is', 'isn', 'it', 'its', 'itself', 'just', 'me', 'might',
        'more', 'most', 'must', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off',
        'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over',
        'own', 'same', 'she', 'should', 'shouldn', 'so', 'some', 'such', 'than', 'that',
        'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they',
        'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was',
        'wasn', 'we', 'were', 'weren', 'what', 'when', 'where', 'which', 'while', 'who',
        'whom', 'why', 'will', 'with', 'won', 'would', 'wouldn', 'you', 'your', 'yours',
        'yourself', 'yourselves',
        # Domain-specific stopwords
        'experience', 'years', 'working', 'work', 'worked', 'skills', 'skill', 'knowledge',
        'understanding', 'strong', 'good', 'excellent', 'proficient', 'familiar', 'ability',
        'able', 'capable', 'responsible', 'responsibilities', 'duties', 'role', 'position',
        'job', 'company', 'team', 'project', 'projects', 'developed', 'develop', 'development',
        'using', 'used', 'use', 'including', 'include', 'includes', 'various', 'multiple',
        'several', 'many', 'different', 'related', 'relevant', 'required', 'requirements',
        'preferred', 'desired', 'must', 'should', 'will', 'can', 'may', 'need', 'needs'
    }
    
    # Triage thresholds (configurable)
    THRESHOLD_EXTREME_MISMATCH = 0.05  # < 5% overlap → Auto-reject
    THRESHOLD_POOR_MATCH = 0.15        # 5-15% overlap → Flag for review
    THRESHOLD_MODERATE_MATCH = 0.30    # 15-30% overlap → Process with low priority
    # > 30% overlap → Process with normal priority
    
    # Minimum CV length (words)
    MIN_CV_LENGTH = 50
    
    def __init__(
        self,
        extreme_threshold: float = None,
        poor_threshold: float = None,
        moderate_threshold: float = None,
        min_cv_length: int = None
    ):
        """
        Initialize Enhanced Triage Engine
        
        Args:
            extreme_threshold: Threshold for extreme mismatch (default: 0.05)
            poor_threshold: Threshold for poor match (default: 0.15)
            moderate_threshold: Threshold for moderate match (default: 0.30)
            min_cv_length: Minimum CV length in words (default: 50)
        """
        self.extreme_threshold = extreme_threshold or self.THRESHOLD_EXTREME_MISMATCH
        self.poor_threshold = poor_threshold or self.THRESHOLD_POOR_MATCH
        self.moderate_threshold = moderate_threshold or self.THRESHOLD_MODERATE_MATCH
        self.min_cv_length = min_cv_length or self.MIN_CV_LENGTH
        
        logger.info(f"Enhanced Triage Engine initialized with thresholds: "
                   f"extreme={self.extreme_threshold}, poor={self.poor_threshold}, "
                   f"moderate={self.moderate_threshold}")
    
    def extract_keywords(self, text: str) -> Set[str]:
        """
        Extract meaningful keywords from text
        
        Args:
            text: Input text (CV or JD)
        
        Returns:
            Set of keywords (5+ chars, excluding stopwords)
        """
        if not text:
            return set()
        
        # Convert to lowercase
        text_lower = text.lower()
        
        # Extract words (alphanumeric + common tech symbols)
        # Matches: python, c++, .net, node.js, asp.net, etc.
        words = re.findall(r'\b[a-z0-9#+.\-]+\b', text_lower)
        
        # Filter keywords
        keywords = set()
        for word in words:
            # Skip if too short (< 5 chars) unless it's a known tech term
            if len(word) < 5:
                # Allow short tech terms: c++, c#, js, go, r, ai, ml, ci, cd, aws, gcp, sql
                tech_terms = {'c++', 'c#', 'js', 'go', 'r', 'ai', 'ml', 'ci', 'cd', 
                             'aws', 'gcp', 'sql', 'api', 'ui', 'ux', 'ios', 'php',
                             'css', 'html', 'xml', 'json', 'rest', 'soap', 'grpc',
                             '.net', 'asp', 'jsp', 'j2ee'}
                if word not in tech_terms:
                    continue
            
            # Skip stopwords
            if word in self.STOPWORDS:
                continue
            
            # Skip pure numbers
            if word.isdigit():
                continue
            
            keywords.add(word)
        
        return keywords
    
    def compute_relevance_score(
        self,
        cv_keywords: Set[str],
        jd_keywords: Set[str]
    ) -> float:
        """
        Compute relevance score using set intersection
        
        Args:
            cv_keywords: Keywords extracted from CV
            jd_keywords: Keywords extracted from JD
        
        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        if not jd_keywords:
            logger.warning("JD has no keywords, returning 0.0 relevance")
            return 0.0
        
        if not cv_keywords:
            logger.warning("CV has no keywords, returning 0.0 relevance")
            return 0.0
        
        # Compute intersection
        intersection = cv_keywords.intersection(jd_keywords)
        
        # Overlap ratio = intersection / JD keywords
        # (What percentage of JD requirements does the CV mention?)
        overlap_ratio = len(intersection) / len(jd_keywords)
        
        logger.debug(f"Relevance score: {overlap_ratio:.2%} "
                    f"({len(intersection)}/{len(jd_keywords)} keywords matched)")
        
        return overlap_ratio
    
    def should_process(
        self,
        cv_text: str,
        job_description: str
    ) -> Tuple[bool, str, float]:
        """
        Determine if CV should be processed based on relevance
        
        Args:
            cv_text: CV text content
            job_description: Job description text
        
        Returns:
            Tuple of (should_process, reason, relevance_score)
            - should_process: True if CV should be processed, False to reject
            - reason: Human-readable reason for decision
            - relevance_score: Overlap ratio (0.0 to 1.0)
        """
        # Check 1: CV length validation
        cv_words = cv_text.split()
        if len(cv_words) < self.min_cv_length:
            reason = (f"CV too short ({len(cv_words)} words, minimum {self.min_cv_length}). "
                     f"Likely corrupted or incomplete file.")
            logger.info(f"REJECT: {reason}")
            return False, reason, 0.0
        
        # Check 2: Extract keywords
        cv_keywords = self.extract_keywords(cv_text)
        jd_keywords = self.extract_keywords(job_description)
        
        if not jd_keywords:
            reason = "Job description has no extractable keywords. Cannot perform triage."
            logger.warning(reason)
            return True, reason, 1.0  # Process anyway if JD is unclear
        
        if not cv_keywords:
            reason = "CV has no extractable keywords. Likely corrupted or non-text file."
            logger.info(f"REJECT: {reason}")
            return False, reason, 0.0
        
        # Check 3: Compute relevance score
        relevance_score = self.compute_relevance_score(cv_keywords, jd_keywords)
        
        # Check 4: Apply multi-tier thresholds
        if relevance_score < self.extreme_threshold:
            # Tier 1: Extreme mismatch → Auto-reject
            reason = (f"Extreme mismatch detected ({relevance_score:.1%} overlap). "
                     f"CV appears irrelevant for this role. Auto-rejected to save API quota.")
            logger.info(f"REJECT (Tier 1): {reason}")
            return False, reason, relevance_score
        
        elif relevance_score < self.poor_threshold:
            # Tier 2: Poor match → Flag for review (but still process)
            reason = (f"Poor match ({relevance_score:.1%} overlap). "
                     f"CV has minimal relevance but will be processed for review.")
            logger.info(f"PROCESS (Tier 2 - Low Priority): {reason}")
            return True, reason, relevance_score
        
        elif relevance_score < self.moderate_threshold:
            # Tier 3: Moderate match → Process with low priority
            reason = (f"Moderate match ({relevance_score:.1%} overlap). "
                     f"CV shows some relevance, processing with low priority.")
            logger.info(f"PROCESS (Tier 3 - Low Priority): {reason}")
            return True, reason, relevance_score
        
        else:
            # Tier 4: Good match → Process with normal priority
            reason = (f"Good match ({relevance_score:.1%} overlap). "
                     f"CV shows strong relevance, processing with normal priority.")
            logger.info(f"PROCESS (Tier 4 - Normal Priority): {reason}")
            return True, reason, relevance_score
    
    def get_priority_from_score(self, relevance_score: float) -> int:
        """
        Get job priority based on relevance score
        
        Args:
            relevance_score: Overlap ratio (0.0 to 1.0)
        
        Returns:
            Priority level (0=HIGH, 5=NORMAL, 10=LOW)
        """
        if relevance_score >= self.moderate_threshold:
            return 5  # NORMAL priority (good match)
        elif relevance_score >= self.poor_threshold:
            return 10  # LOW priority (moderate/poor match)
        else:
            return 10  # LOW priority (should be rejected, but if processed)
    
    def get_triage_stats(
        self,
        cv_texts: list,
        job_description: str
    ) -> dict:
        """
        Get triage statistics for a batch of CVs
        
        Args:
            cv_texts: List of CV text contents
            job_description: Job description text
        
        Returns:
            Dictionary with triage statistics
        """
        stats = {
            'total_cvs': len(cv_texts),
            'rejected': 0,
            'tier1_extreme_mismatch': 0,
            'tier2_poor_match': 0,
            'tier3_moderate_match': 0,
            'tier4_good_match': 0,
            'avg_relevance_score': 0.0,
            'api_calls_saved': 0
        }
        
        total_score = 0.0
        
        for cv_text in cv_texts:
            should_process, reason, score = self.should_process(cv_text, job_description)
            total_score += score
            
            if not should_process:
                stats['rejected'] += 1
                stats['api_calls_saved'] += 1
                if score < self.extreme_threshold:
                    stats['tier1_extreme_mismatch'] += 1
            else:
                if score >= self.moderate_threshold:
                    stats['tier4_good_match'] += 1
                elif score >= self.poor_threshold:
                    stats['tier3_moderate_match'] += 1
                else:
                    stats['tier2_poor_match'] += 1
        
        if stats['total_cvs'] > 0:
            stats['avg_relevance_score'] = round(total_score / stats['total_cvs'], 3)
        
        stats['rejection_rate'] = round(stats['rejected'] / stats['total_cvs'] * 100, 1) if stats['total_cvs'] > 0 else 0
        stats['api_quota_saved_percent'] = stats['rejection_rate']
        
        return stats


# Singleton instance for easy import
_triage_engine = None

def get_triage_engine() -> EnhancedTriageEngine:
    """Get or create singleton triage engine instance"""
    global _triage_engine
    if _triage_engine is None:
        _triage_engine = EnhancedTriageEngine()
    return _triage_engine
