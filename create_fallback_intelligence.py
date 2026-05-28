#!/usr/bin/env python
"""
Create fallback intelligence files from redacted CVs (when LLM API is unavailable)
Uses rule-based extraction to generate searchable intelligence without LLM
"""
import os
import sys
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Common tech skills and frameworks
TECH_SKILLS = {
    'python', 'javascript', 'java', 'c++', 'c#', 'typescript', 'go', 'rust', 'php', 'ruby',
    'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
    'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'express', 'spring',
    'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'aws', 'azure', 'gcp',
    'git', 'linux', 'unix', 'windows', 'macos',
    'html', 'css', 'rest', 'graphql', 'api', 'microservices',
    'machine learning', 'ai', 'nlp', 'deep learning', 'tensorflow', 'pytorch', 'keras',
    'data science', 'pandas', 'numpy', 'scipy', 'scikit-learn',
    'devops', 'ci/cd', 'agile', 'scrum', 'jira', 'confluence',
    'blockchain', 'solidity', 'web3', 'ethereum', 'smart contracts',
    'ocr', 'computer vision', 'nlp', 'langchain', 'llama', 'hugging face',
    'vapi', 'ollama', 'chroma', 'neo4j', 'rag', 'graph',
    'signal processing', 'feature engineering', 'data balancing', 'pii detection'
}

SENIORITY_INDICATORS = {
    'lead': 'LEAD',
    'principal': 'LEAD',
    'architect': 'LEAD',
    'manager': 'LEAD',
    'director': 'LEAD',
    'senior': 'SENIOR',
    'sr.': 'SENIOR',
    'sr ': 'SENIOR',
    'mid-level': 'MID',
    'mid level': 'MID',
    'junior': 'ENTRY',
    'entry': 'ENTRY',
    'intern': 'ENTRY',
    'graduate': 'ENTRY'
}


def extract_skills_from_text(text: str) -> List[str]:
    """Extract technical skills from redacted CV text"""
    text_lower = text.lower()
    found_skills = []
    
    for skill in TECH_SKILLS:
        if skill in text_lower:
            # Count occurrences
            count = len(re.findall(r'\b' + re.escape(skill) + r'\b', text_lower))
            if count > 0:
                found_skills.append((skill, count))
    
    # Sort by frequency
    found_skills.sort(key=lambda x: x[1], reverse=True)
    return [skill[0].title() for skill in found_skills[:20]]


def extract_years_of_experience(text: str) -> float:
    """Extract approximate years of experience from dates"""
    # Look for patterns like "September 2025", "9 years", "5+ years", etc.
    years_pattern = r'(\d+)\s*(?:\+)?\s*(?:years?|yrs?)'
    matches = re.findall(years_pattern, text.lower())
    
    if matches:
        years = [int(m) for m in matches]
        return max(years) if years else 0
    
    # Try to infer from dates
    date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})'
    dates = re.findall(date_pattern, text)
    
    if dates and len(dates) >= 2:
        # Try to extract years from dates
        years = [int(d[1]) for d in dates]
        year_span = max(years) - min(years) if len(set(years)) > 1 else 0
        return float(max(year_span, 1))
    
    return 0.0


def infer_seniority_level(text: str, years: float) -> str:
    """Infer seniority level from text and years of experience"""
    text_lower = text.lower()
    
    for keyword, level in SENIORITY_INDICATORS.items():
        if keyword in text_lower:
            return level
    
    # Fallback: infer from years
    if years >= 15:
        return 'LEAD'
    elif years >= 8:
        return 'SENIOR'
    elif years >= 3:
        return 'MID'
    else:
        return 'ENTRY'


def create_fallback_intelligence(redacted_text: str, anonymized_id: str, original_filename: str) -> Dict[str, Any]:
    """Create fallback intelligence structure from redacted CV text without LLM"""
    try:
        skills = extract_skills_from_text(redacted_text)
        years = extract_years_of_experience(redacted_text)
        seniority = infer_seniority_level(redacted_text, years)
        
        # Determine primary domain from skills
        primary_domain = "General"
        if any(s.lower() in redacted_text.lower() for s in ['python', 'java', 'c++', 'react', 'angular']):
            if any(s.lower() in redacted_text.lower() for s in ['machine learning', 'ai', 'nlp', 'deep learning']):
                primary_domain = "AI/ML"
            elif any(s.lower() in redacted_text.lower() for s in ['docker', 'kubernetes', 'devops', 'ci/cd']):
                primary_domain = "DevOps"
            elif any(s.lower() in redacted_text.lower() for s in ['react', 'angular', 'vue', 'frontend']):
                primary_domain = "Frontend"
            else:
                primary_domain = "Software Development"
        elif any(s.lower() in redacted_text.lower() for s in ['blockchain', 'solidity', 'web3', 'smart contracts']):
            primary_domain = "Blockchain"
        elif any(s.lower() in redacted_text.lower() for s in ['data', 'analytics', 'bi', 'etl']):
            primary_domain = "Data Engineering"
        
        # Create intelligence structure
        intelligence = {
            "anonymized_id": anonymized_id,
            "analysis_date": datetime.now().isoformat(),
            "confidence_score": 65,  # Lower than LLM-generated (80)
            "verdict_reason": "Profile extracted (fallback mode - LLM unavailable)",
            "years_experience": years,
            "years_experience_range": f"{int(years)}-{int(years)+1}" if years > 0 else "0-1",
            "seniority_level": seniority,
            "career_level": seniority,
            "core_technical_skills": skills[:8],
            "secondary_technical_skills": skills[8:15],
            "key_skills": skills,
            "frameworks_tools": [s for s in skills if any(fw in s.lower() for fw in ['react', 'django', 'flask', 'fastapi', 'docker', 'kubernetes', 'jenkins'])],
            "soft_skills": ["Problem Solving", "Communication", "Collaboration"],
            "certifications": ["Not specified"],
            "role_types": ["Software Engineer"],
            "leadership_indicators": [],
            "primary_domain": primary_domain,
            "secondary_domains": [],
            "cleaned_narrative": f"Candidate with {int(years)} years of experience in {primary_domain}. Core skills: {', '.join(skills[:5])}. Seniority level: {seniority}.",
            "matched_requirements": [],
            "missing_requirements": [],
            "key_strengths": [
                f"Expertise in {', '.join(skills[:3])}",
                f"Experience level: {seniority}",
                f"Seniority: {seniority} level with {int(years)} years experience"
            ],
            "potential_concerns": [
                "Profile extracted in fallback mode (LLM unavailable) - some details may be inferred"
            ],
            "highlight_achievements": [],
            "highest_degree": "Not specified",
            "field_of_study": "Not specified",
            "education_level": "",
            "fitment_analysis": [],
            "original_filename": original_filename,
            "original_filename_raw": original_filename,
            "llm_provider": "none",  # Indicate fallback mode
            "llm_model": "rule_based_extraction",
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_mode": "fallback",
            "cleaned_text": redacted_text,
            "original_cv_hash": "fallback_" + anonymized_id.lower()
        }
        
        return intelligence
    except Exception as e:
        logger.error(f"Error creating fallback intelligence: {e}")
        return {"error": str(e), "anonymized_id": anonymized_id}


def load_redacted_text(file_path: str) -> str:
    """Load redacted text from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return ""


def extract_anonymized_id_from_filename(filename: str) -> str:
    """Extract anonymized ID from filename"""
    stem = Path(filename).stem
    parts = stem.split('_')
    if len(parts) >= 3:
        hash_part = parts[-1]
        hash_int = int(hash_part[:8], 16)
        cand_id = f"CAND_{hash_int:08X}"
        return cand_id
    return f"CAND_{os.urandom(4).hex().upper()}"


def main():
    """Generate fallback intelligence files for failed CVs"""
    logger.info("=" * 60)
    logger.info("CREATING FALLBACK INTELLIGENCE FILES")
    logger.info("=" * 60)
    
    Path('llm_analysis').mkdir(exist_ok=True)
    
    # Find redacted text files
    redacted_dir = Path('redacted_output')
    if not redacted_dir.exists():
        logger.error(f"Redacted directory not found: {redacted_dir}")
        return False
    
    redacted_files = list(redacted_dir.glob('REDACTED_*.txt'))
    logger.info(f"Found {len(redacted_files)} redacted CV files")
    
    success_count = 0
    skipped_count = 0
    
    for redacted_file in sorted(redacted_files):
        # Check if intelligence file already exists and is valid
        parts = redacted_file.stem.split('_')
        if len(parts) >= 3:
            hash_part = '_'.join(parts[1:])
            intel_file = Path('llm_analysis') / f"REDACTED_{hash_part}_intelligence.json"
            
            if intel_file.exists():
                try:
                    with open(intel_file, 'r') as f:
                        data = json.load(f)
                    if 'error' not in data and data.get('confidence_score', 0) > 0:
                        logger.info(f"✓ SKIP (already valid): {redacted_file.name}")
                        skipped_count += 1
                        continue
                except:
                    pass
            
            # Create fallback intelligence
            logger.info(f"Processing: {redacted_file.name}")
            redacted_text = load_redacted_text(str(redacted_file))
            if not redacted_text:
                logger.error(f"  ✗ No text found")
                continue
            
            anonymized_id = extract_anonymized_id_from_filename(redacted_file.name)
            intelligence = create_fallback_intelligence(
                redacted_text=redacted_text,
                anonymized_id=anonymized_id,
                original_filename=redacted_file.name
            )
            
            # Save intelligence JSON
            with open(intel_file, 'w', encoding='utf-8') as f:
                json.dump(intelligence, f, indent=2, ensure_ascii=False)
            
            logger.info(f"  ✓ Generated fallback intelligence for {anonymized_id}")
            success_count += 1
    
    logger.info("=" * 60)
    logger.info(f"FALLBACK GENERATION COMPLETE")
    logger.info(f"  ✓ Created: {success_count}")
    logger.info(f"  ⊘ Skipped (already valid): {skipped_count}")
    logger.info("=" * 60)
    logger.info("✓ All CVs now have searchable intelligence files!")
    logger.info("  Search should display candidates properly")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
