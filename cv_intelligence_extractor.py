"""
CV Intelligence Extractor - Production version with deep analysis
Analyzes anonymized CVs against job descriptions using LLM
Outputs structured JSON with confidence scores and evidence-based verdicts
"""
import os
import json
import hashlib
import random
import string
import re
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime

# Import LLM batch processor for API calls
from llm_batch_processor import LLMBatchProcessor

logger = logging.getLogger(__name__)

# Redaction markers that indicate a CV has been properly anonymized
REDACTION_MARKERS = [
    "[REDACTED", "[NAME]", "[REDACTED_NAME]", "[REDACTED_CONTACT",
    "[REDACTED_EMAIL]", "[REDACTED_PHONE]", "[REDACTED_ADDRESS]",
    "[REDACTED_SOCIAL]", "[REDACTED_LINKEDIN]", "[REDACTED_URL]",
    "[REDACTED_CONTACT_LINE]", "[REDACTED_LOCATION]"
]


def is_cv_anonymized(cv_text: str) -> bool:
    """
    Check if a CV has been properly anonymized by looking for redaction markers.
    
    Args:
        cv_text: The CV text to check
        
    Returns:
        True if the CV contains redaction markers (is anonymized), False otherwise
    """
    if not cv_text or not cv_text.strip():
        return False
    return any(marker in cv_text for marker in REDACTION_MARKERS)


def sanitize_filename_for_db(filename: str) -> str:
    """
    Strip PII from filenames before storing in database.
    Original filenames may contain real names - replace with anonymized version.
    
    Args:
        filename: Original filename that may contain real names
        
    Returns:
        Sanitized filename safe for database storage
    """
    if not filename:
        return "unknown"
    # Keep only the REDACTED_ prefix and extension, strip embedded real names
    import re
    # If it starts with REDACTED_, keep the timestamp part only
    match = re.match(r'(REDACTED_\d{8}_\d{6}_)', filename)
    if match:
        return match.group(1) + "anonymized_cv.txt"
    # If no REDACTED prefix, just use a generic name
    return "anonymized_cv.txt"


class CVIntelligenceExtractor:
    """Extract structured intelligence from anonymized CVs using LLM with deep analysis"""
    
    def __init__(self, api_provider: str = "gemini", api_key: str = None, model: str = None):
        """
        Initialize the CV Intelligence Extractor
        
        Args:
            api_provider: 'openai', 'anthropic', 'gemini', or 'ollama' (default: gemini)
            api_key: API key (reads from env if not provided, not needed for Ollama)
            model: Specific model to use (optional)
        """
        self.api_provider = api_provider
        self.llm_processor = LLMBatchProcessor(
            api_provider=api_provider,
            api_key=api_key,
            model=model
        )
        self.model = model or self.llm_processor.model
        
    def _generate_anonymized_id(self) -> str:
        """
        Generate unique anonymized candidate ID (e.g., "CAND_882")
        
        Returns:
            Anonymized ID string
        """
        # Generate random 3-digit number
        number = random.randint(100, 999)
        return f"CAND_{number}"
    
    def _hash_job_description(self, job_description: str) -> str:
        """
        Create hash of job description for tracking
        
        Args:
            job_description: The JD text
            
        Returns:
            SHA256 hash (first 16 chars)
        """
        return hashlib.sha256(job_description.encode()).hexdigest()[:16]
    
    def _hash_cv_content(self, cv_text: str) -> str:
        """
        Create hash of original CV content for audit trail
        
        Args:
            cv_text: The CV content
            
        Returns:
            SHA256 hash (full 64 chars for audit trail)
        """
        return hashlib.sha256(cv_text.encode()).hexdigest()
        
    def _create_extraction_prompt(self, cv_text: str, job_description: str, anonymized_id: str) -> str:
        """
        Create a detailed extraction prompt that produces Gemini-quality fitment analysis.
        The output is structured prose that gets parsed into JSON.
        """
        prompt = f"""You are a senior technical recruiter performing a detailed fitment analysis. Compare the anonymized professional profile against the job description below.

IMPORTANT RULES:
- The CV is already anonymized (all PII removed). NEVER output names, emails, phone numbers, addresses, or company locations.
- If you cannot determine something, state "Not specified" — NEVER invent details.
- Be thorough and evidence-based. Cite specific technologies, years, and project details from the CV.
- Provide a DETAILED category-by-category comparison like a professional recruitment report.
- The Overall Assessment MUST be an original analytical summary you write — do NOT copy-paste text from the CV.

OUTPUT FORMAT (FOLLOW THIS STRUCTURE EXACTLY):

SECTION 1 – Overall Assessment:
[Write a 2-3 paragraph ORIGINAL executive summary in your own words covering:
- Who the candidate is (years of experience, primary role, key expertise areas)
- Why they are / are not a good fit for this specific role
- One line recommendation
IMPORTANT: This must be YOUR analytical summary, NOT copied text from the CV. Synthesize the information into a professional recruiter assessment.]

SECTION 2 – Fitment Analysis Table:
For EACH major requirement category in the JD, provide a line in this exact format:
CATEGORY: [category name]
JD_REQUIRES: [what the JD asks for]
CANDIDATE_HAS: [what the candidate actually has, with evidence]
MATCH_STATUS: [FULL_MATCH | PARTIAL_MATCH | NO_MATCH]

(Create one entry for each of these categories, adapting to the JD:
- Total Experience
- Core Programming Languages
- Primary Domain / Industry
- Frameworks & Tools
- Architecture & Design Patterns
- Cloud / Infrastructure
- Leadership & Team Management
- Education / Certifications
- Any other JD-specific categories)

SECTION 3 – Key Strengths:
- [Strength 1 with specific evidence from CV]
- [Strength 2 with specific evidence from CV]
- [Strength 3 with specific evidence from CV]
- [Strength 4 with specific evidence from CV (if applicable)]

SECTION 4 – Potential Gaps / Areas to Verify:
- [Gap 1: what is missing or unclear, and its impact]
- [Gap 2: what is missing or unclear, and its impact]
(If no gaps: "No critical gaps identified.")

SECTION 5 – Experience Breakdown:
Years of Experience: [exact number, e.g., "9 years" or "5-6 years"]
Seniority Level: [ENTRY: 0-2yrs | MID: 2-5yrs | SENIOR: 5-10yrs | LEAD: 10-15yrs | EXECUTIVE: 15+yrs]
Core Technical Skills: [List top 10 technical skills from CV]
Secondary Skills: [List additional tools, frameworks, soft skills]
Primary Domain: [Main industry/sector e.g., "Automotive Embedded", "Web Development"]
Leadership Indicators: [List concrete evidence: "Led 5-person team", "Mentored 3 juniors", or "None mentioned"]

FINAL RECOMMENDATION:
[SHORTLIST | BACKUP | REVIEW]
Confidence: [0-100]%
Match Score: [0-100]%

Reason: [2-3 sentences with specific evidence. First sentence: overall verdict with primary reason. Second: key matching evidence. Third: what tips the balance.]

===== DECISION RULES =====
- SHORTLIST: 80%+ requirements matched with strong evidence. Ready for interview.
- BACKUP: 60-79% requirements matched. Good candidate but has some gaps.
- REVIEW: <60% matched OR unclear/insufficient CV data → human must decide.
- If Confidence <70%, automatically use REVIEW regardless of match score.
- NEVER use REJECT — when in doubt, use REVIEW.

---

JOB DESCRIPTION:
{job_description}

---

ANONYMIZED PROFESSIONAL PROFILE:
{cv_text}

---

CANDIDATE ID: {anonymized_id}
ANALYSIS DATE: {datetime.now().isoformat()}"""
        
        return prompt
    
    def _parse_prose_response(self, prose_response: str, anonymized_id: str) -> Dict:
        """
        Parse detailed prose LLM response into structured JSON.
        Extracts fitment table, strengths, gaps, and all structured fields.
        """
        try:
            # Extract verdict
            verdict_match = re.search(r'FINAL RECOMMENDATION:\s*\n?\[?(SHORTLIST|BACKUP|REVIEW)\]?', prose_response, re.IGNORECASE)
            verdict = verdict_match.group(1).upper() if verdict_match else "REVIEW"
            
            # Extract confidence score
            confidence_match = re.search(r'Confidence:\s*\[?(\d+)\]?%', prose_response)
            confidence_score = int(confidence_match.group(1)) if confidence_match else 50
            
            # Extract match score
            match_match = re.search(r'Match Score:\s*\[?(\d+)\]?%', prose_response)
            match_score = int(match_match.group(1)) if match_match else 50
            
            # Extract verdict reason
            reason_match = re.search(r'Reason:\s*(.+?)(?:\n\n|={3,}|$)', prose_response, re.DOTALL)
            verdict_reason = reason_match.group(1).strip() if reason_match else "See detailed analysis above"
            
            # Extract years of experience
            years_match = re.search(r'Years of Experience:\s*\[?([0-9.]+(?:\s*-\s*[0-9.]+)?)\s*(?:years?)?\]?', prose_response, re.IGNORECASE)
            if years_match:
                years_str = years_match.group(1).replace(' ', '')
                if '-' in years_str:
                    start, end = years_str.split('-')
                    years_experience = (float(start) + float(end)) / 2
                    years_experience_range = years_str
                else:
                    years_experience = float(years_str)
                    years_experience_range = f"{int(years_experience)}-{int(years_experience)+1}"
            else:
                years_experience = 0
                years_experience_range = "Not specified"
            
            # Extract seniority level
            seniority_match = re.search(r'Seniority Level:\s*\[?(ENTRY|MID|SENIOR|LEAD|EXECUTIVE)\]?', prose_response, re.IGNORECASE)
            seniority_level = seniority_match.group(1).upper() if seniority_match else "MID"
            
            # Extract core technical skills (with or without brackets)
            skills_section = re.search(r'Core Technical Skills:\s*\[?(.+?)\]?\s*(?:\n|$)', prose_response, re.DOTALL)
            if skills_section:
                skills_text = skills_section.group(1).strip()
                # Handle multi-line or comma-separated skills
                core_technical_skills = [s.strip().strip('"\'[]') for s in skills_text.split(',') if s.strip() and s.strip() not in ['[', ']']]
                core_technical_skills = [s for s in core_technical_skills if s]  # Remove empty
            else:
                core_technical_skills = []
            
            # Extract secondary skills (with or without brackets)
            secondary_section = re.search(r'Secondary Skills:\s*\[?(.+?)\]?\s*(?:\n|$)', prose_response, re.DOTALL)
            if secondary_section:
                sec_text = secondary_section.group(1).strip()
                secondary_technical_skills = [s.strip().strip('"\'[]') for s in sec_text.split(',') if s.strip() and s.strip() not in ['[', ']']]
                secondary_technical_skills = [s for s in secondary_technical_skills if s]
            else:
                secondary_technical_skills = []
            
            # Extract primary domain
            domain_match = re.search(r'Primary Domain:\s*\[?([^\]\n]+)\]?', prose_response, re.IGNORECASE)
            primary_domain = domain_match.group(1).strip().strip('"\'') if domain_match else ""
            
            # Extract leadership indicators (with or without brackets)
            leadership_section = re.search(r'Leadership Indicators:\s*\[?(.+?)\]?\s*(?:\n|$)', prose_response, re.DOTALL)
            if leadership_section:
                leadership_text = leadership_section.group(1).strip()
                if leadership_text.lower() in ['none mentioned', 'none mentioned.', 'none', 'n/a', 'not specified']:
                    leadership_indicators = []
                else:
                    leadership_indicators = [s.strip().strip('"\'[]') for s in leadership_text.split(',') if s.strip()]
                    leadership_indicators = [s for s in leadership_indicators if s]
            else:
                leadership_indicators = []
            
            # Extract SECTION 1 (Overall Assessment)
            section1_match = re.search(r'SECTION 1[^\n]*\n(.+?)(?=SECTION 2|FINAL RECOMMENDATION|$)', prose_response, re.DOTALL)
            cleaned_narrative = section1_match.group(1).strip() if section1_match else ""
            
            # ===== NEW: Extract Fitment Analysis Table (SECTION 2) =====
            fitment_analysis = []
            section2_match = re.search(r'SECTION 2[^\n]*\n(.+?)(?=SECTION 3|Key Strengths|$)', prose_response, re.DOTALL)
            if section2_match:
                section2_text = section2_match.group(1)
                # Parse CATEGORY/JD_REQUIRES/CANDIDATE_HAS/MATCH_STATUS blocks
                # Support both plain "CATEGORY:" and dash-prefixed "- CATEGORY:" formats
                categories = re.findall(
                    r'-?\s*CATEGORY:\s*(.+?)\n-?\s*JD_REQUIRES:\s*(.+?)\n-?\s*CANDIDATE_HAS:\s*(.+?)\n-?\s*MATCH_STATUS:\s*(FULL_MATCH|PARTIAL_MATCH|NO_MATCH)',
                    section2_text, re.DOTALL
                )
                for cat, jd_req, cand_has, status in categories:
                    fitment_analysis.append({
                        "category": cat.strip(),
                        "jd_requirement": jd_req.strip(),
                        "candidate_profile": cand_has.strip(),
                        "match_status": status.strip()
                    })
            
            # ===== NEW: Extract Key Strengths (SECTION 3) =====
            key_strengths = []
            section3_match = re.search(r'(?:SECTION 3|Key Strengths)[^\n]*\n(.+?)(?=SECTION 4|Potential Gaps|SECTION 5|Experience Breakdown|FINAL|$)', prose_response, re.DOTALL)
            if section3_match:
                for line in section3_match.group(1).strip().split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*'):
                        key_strengths.append(line.lstrip('-* ').strip())
            
            # ===== NEW: Extract Potential Gaps (SECTION 4) =====
            potential_concerns = []
            section4_match = re.search(r'(?:SECTION 4|Potential Gaps)[^\n]*\n(.+?)(?=SECTION 5|Experience Breakdown|FINAL|$)', prose_response, re.DOTALL)
            if section4_match:
                for line in section4_match.group(1).strip().split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*'):
                        potential_concerns.append(line.lstrip('-* ').strip())
            
            # Extract matched/missing requirements from fitment table
            matched_requirements = [f["category"] for f in fitment_analysis if f["match_status"] == "FULL_MATCH"]
            missing_requirements = [f["category"] for f in fitment_analysis if f["match_status"] == "NO_MATCH"]
            
            # Count match stats
            total_categories = len(fitment_analysis)
            full_matches = len(matched_requirements)
            partial_matches = len([f for f in fitment_analysis if f["match_status"] == "PARTIAL_MATCH"])
            no_matches = len(missing_requirements)
            
            # Build structured response
            intelligence = {
                "anonymized_id": anonymized_id,
                "analysis_date": datetime.now().isoformat(),
                
                # Core fields
                "verdict": verdict,
                "confidence_score": confidence_score,
                "match_score": match_score,
                "verdict_reason": verdict_reason,
                
                # Experience
                "years_experience": years_experience,
                "years_experience_range": years_experience_range,
                "seniority_level": seniority_level,
                
                # Skills
                "core_technical_skills": core_technical_skills,
                "secondary_technical_skills": secondary_technical_skills,
                "leadership_indicators": leadership_indicators,
                
                # Domain
                "primary_domain": primary_domain,
                "secondary_domains": [],
                
                # Analysis
                "cleaned_narrative": cleaned_narrative,
                "matched_requirements": matched_requirements,
                "missing_requirements": missing_requirements,
                "key_strengths": key_strengths,
                "potential_concerns": potential_concerns,
                
                # NEW: Detailed fitment analysis table
                "fitment_analysis": fitment_analysis,
                "fitment_summary": {
                    "total_categories": total_categories,
                    "full_match": full_matches,
                    "partial_match": partial_matches,
                    "no_match": no_matches,
                    "match_rate": round((full_matches + partial_matches * 0.5) / total_categories * 100, 1) if total_categories > 0 else 0
                },
                
                # Full prose output for recruiter review
                "detailed_analysis": prose_response
            }
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error parsing prose response: {e}")
            return {
                "anonymized_id": anonymized_id,
                "analysis_date": datetime.now().isoformat(),
                "verdict": "REVIEW",
                "confidence_score": 30,
                "match_score": 50,
                "verdict_reason": "Analysis parsing failed - requires human review",
                "detailed_analysis": prose_response,
                "parse_error": str(e)
            }
    
    def extract_intelligence(
        self, 
        cv_text: str, 
        job_description: str,
        original_filename: str = None
    ) -> Dict:
        """
        Extract structured intelligence from a CV with deep analysis and audit trail.
        
        IMPORTANT: Only processes anonymized CVs. If the CV is not anonymized,
        returns an error asking the user to anonymize first.
        
        Args:
            cv_text: Anonymized CV content (must contain [REDACTED_...] markers)
            job_description: Job description to match against
            original_filename: Original filename (for backend tracking only)
            
        Returns:
            Dictionary with structured CV intelligence + full audit trail
        """
        try:
            # CRITICAL: Verify CV is anonymized before processing
            if not is_cv_anonymized(cv_text):
                logger.error("CV is not anonymized. Cannot process non-anonymized CVs.")
                return {
                    "error": "CV_NOT_ANONYMIZED",
                    "error_message": (
                        "This CV has not been anonymized. Please run the CV through the "
                        "redaction pipeline first (Upload → Redact PII) before extracting "
                        "intelligence. Only anonymized CVs can be stored in the database."
                    ),
                    "anonymized_id": self._generate_anonymized_id(),
                    "original_filename": sanitize_filename_for_db(original_filename) if original_filename else "unknown"
                }
            
            # Generate anonymized ID
            anonymized_id = self._generate_anonymized_id()
            
            # Create extraction prompt (store for audit trail)
            prompt = self._create_extraction_prompt(cv_text, job_description, anonymized_id)
            
            # Hash original CV for audit trail
            original_cv_hash = self._hash_cv_content(cv_text)
            
            # Call LLM
            logger.info(f"Analyzing {anonymized_id}...")
            raw_llm_response = self.llm_processor.generate_analysis(prompt)
            
            # Parse prose response (new human-readable format)
            try:
                # Use prose parser instead of JSON
                intelligence = self._parse_prose_response(raw_llm_response, anonymized_id)
                
                # Add metadata — sanitize filename to remove any real names
                intelligence["original_filename"] = sanitize_filename_for_db(original_filename) if original_filename else "unknown"
                intelligence["original_filename_raw"] = original_filename or "unknown"  # Keep raw for local use only
                intelligence["llm_provider"] = self.api_provider
                intelligence["llm_model"] = self.model
                intelligence["extraction_timestamp"] = datetime.now().isoformat()
                intelligence["job_description_hash"] = self._hash_job_description(job_description)
                
                # Store the anonymized CV text for future use (JD comparisons, re-analysis)
                intelligence["cleaned_text"] = cv_text
                
                # Audit Trail (Full Explainability)
                intelligence["original_cv_hash"] = original_cv_hash
                intelligence["llm_prompt_used"] = prompt  # Full prompt for reproducibility
                intelligence["llm_raw_response"] = raw_llm_response  # Raw LLM output
                
                # NO AUTO-REJECT POLICY: Check confidence threshold
                confidence = intelligence.get("confidence_score", 0)
                if confidence < 70:
                    intelligence["requires_human_review"] = True
                    logger.warning(f"⚠️  {anonymized_id}: Low confidence ({confidence}%) → HUMAN REVIEW REQUIRED")
                else:
                    intelligence["requires_human_review"] = False
                
                verdict_status = "🔴 NEEDS REVIEW" if intelligence["requires_human_review"] else intelligence.get('verdict')
                logger.info(f"✓ {anonymized_id}: {verdict_status} (Match: {intelligence.get('match_score')}%, Confidence: {confidence}%)")
                
                return intelligence
                
            except Exception as e:
                logger.error(f"Failed to parse LLM response: {e}")
                logger.error(f"Raw response: {raw_llm_response[:500]}...")
                
                # Return error structure with audit trail
                return {
                    "error": f"PARSE_ERROR: {str(e)}",
                    "raw_response": raw_llm_response[:1000],
                    "anonymized_id": anonymized_id,
                    "original_filename": original_filename or "unknown",
                    "original_cv_hash": original_cv_hash,
                    "llm_prompt_used": prompt,
                    "llm_raw_response": raw_llm_response
                }
                
        except Exception as e:
            logger.error(f"Error extracting intelligence: {e}")
            return {
                "error": str(e),
                "anonymized_id": self._generate_anonymized_id(),
                "original_filename": original_filename or "unknown"
            }
    
    def batch_extract(
        self, 
        cv_files: List[str], 
        job_description: str,
        output_dir: str = "llm_analysis",
        direct_to_supabase: bool = True
    ) -> List[Dict]:
        """
        Process multiple CVs in batch with direct Supabase pipeline
        
        Args:
            cv_files: List of paths to anonymized CV text files
            job_description: Job description to match against
            output_dir: Directory to save individual JSON files
            direct_to_supabase: If True, upload directly to Supabase (if configured)
            
        Returns:
            List of intelligence dictionaries
        """
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Initialize Supabase if requested
        storage = None
        if direct_to_supabase:
            try:
                from supabase_storage import SupabaseStorage
                storage = SupabaseStorage()
                logger.info("✓ Direct Supabase pipeline enabled")
            except Exception as e:
                logger.warning(f"⚠ Supabase not available: {e}. Saving to JSON only.")
        
        for cv_file in cv_files:
            try:
                # Read CV content
                with open(cv_file, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
                
                # Extract intelligence
                intelligence = self.extract_intelligence(
                    cv_text, 
                    job_description,
                    Path(cv_file).name
                )
                
                results.append(intelligence)
                
                # Save individual JSON
                if "error" not in intelligence:
                    # Save to local file
                    output_file = output_path / f"{intelligence['anonymized_id']}_intelligence.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(intelligence, f, indent=2, ensure_ascii=False)
                    logger.info(f"  📁 Saved to {output_file}")
                    
                    # Direct pipeline to Supabase
                    if storage:
                        try:
                            storage.store_intelligence(intelligence)
                            # Store filename mapping (backend only)
                            storage.store_filename_mapping(
                                anonymized_id=intelligence['anonymized_id'],
                                original_filename=Path(cv_file).name,
                                anonymized_filename=Path(cv_file).name
                            )
                            logger.info(f"  ☁️  Uploaded to Supabase")
                        except Exception as e:
                            logger.warning(f"  ⚠ Supabase upload failed: {e}")
                else:
                    logger.warning(f"✗ Error processing {cv_file}: {intelligence.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error processing {cv_file}: {e}")
                results.append({
                    "error": str(e),
                    "anonymized_id": self._generate_anonymized_id(),
                    "original_filename": Path(cv_file).name
                })
        
        # Save batch summary
        summary_file = output_path / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_processed": len(cv_files),
                "successful": len([r for r in results if "error" not in r]),
                "failed": len([r for r in results if "error" in r]),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✓ Batch complete. Summary saved to {summary_file}")
        
        return results


def main():
    """CLI entry point for CV intelligence extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract structured intelligence from anonymized CVs"
    )
    parser.add_argument(
        "cv_files",
        nargs="+",
        help="Path(s) to anonymized CV text file(s)"
    )
    parser.add_argument(
        "--job-description",
        "-jd",
        required=True,
        help="Path to job description file or direct text"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "gemini", "ollama"],
        default="gemini",
        help="LLM provider (default: gemini)"
    )
    parser.add_argument(
        "--api-key",
        help="API key (reads from env if not provided)"
    )
    parser.add_argument(
        "--output-dir",
        default="llm_analysis",
        help="Output directory for intelligence JSON files"
    )
    parser.add_argument(
        "--no-supabase",
        action="store_true",
        help="Disable direct Supabase upload (save to JSON only)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Read job description
    if Path(args.job_description).exists():
        with open(args.job_description, 'r', encoding='utf-8') as f:
            job_description = f.read()
    else:
        job_description = args.job_description
    
    # Create extractor
    extractor = CVIntelligenceExtractor(
        api_provider=args.provider,
        api_key=args.api_key
    )
    
    # Process CVs
    print(f"\n{'='*60}")
    print("CV Intelligence Extraction")
    print(f"{'='*60}")
    print(f"Provider: {args.provider}")
    print(f"CVs to process: {len(args.cv_files)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Direct Supabase Pipeline: {not args.no_supabase}")
    print(f"{'='*60}\n")
    
    results = extractor.batch_extract(
        args.cv_files,
        job_description,
        args.output_dir,
        direct_to_supabase=not args.no_supabase
    )
    
    # Print summary
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    
    print(f"\n{'='*60}")
    print(f"✓ Processed: {len(results)} CVs")
    print(f"✓ Successful: {len(successful)}")
    print(f"✗ Failed: {len(failed)}")
    
    if successful:
        print(f"\n📊 VERDICTS:")
        for result in successful:
            verdict = result.get('verdict', 'UNKNOWN')
            match = result.get('match_score', 0)
            confidence = result.get('confidence_score', 0)
            anonymized_id = result.get('anonymized_id', 'N/A')
            print(f"  {anonymized_id}: {verdict} (Match: {match}%, Confidence: {confidence}%)")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
