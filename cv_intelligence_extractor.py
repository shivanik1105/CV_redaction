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
        Create a human-readable extraction prompt for prose-based LLM analysis
        
        Args:
            cv_text: Anonymized CV content
            job_description: Job description to match against
            anonymized_id: The generated anonymized candidate ID
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a senior technical recruiter. Analyze the anonymized professional profile and job description below.

IMPORTANT RULES:
- The input CV is already anonymized (all PII removed). NEVER output names, emails, phone numbers, addresses, company locations, or institution names.
- If you cannot determine something from the text, state "Not specified" — NEVER invent details.
- Be concise but thorough. Focus on evidence explicitly stated in the profile.

OUTPUT FORMAT (STRICTLY FOLLOW THIS STRUCTURE):

SECTION 1 – General Resume Assessment:
[2-3 paragraphs covering:
- Total years of experience and career progression
- Core technical strengths with specific technologies/tools mentioned
- Notable projects or achievements (with measurable impact if stated)
- One key weakness or gap (e.g., lack of quantifiable metrics, generic descriptions)]

SECTION 2 – Job Description Fit:
Mandatory Skills:
- [Skill 1]: [Matched/Not found] — [brief evidence or "no mention"]
- [Skill 2]: [Matched/Not found] — [brief evidence or "no mention"]
[Continue for all mandatory skills listed in JD]

Secondary Skills:
- [Skill A]: [Partial match/Not found] — [brief context]
- [Skill B]: [Partial match/Not found] — [brief context]
[Continue for nice-to-have skills]

Gap Analysis:
[1-2 sentences: "Primary gap is X" OR "No critical gaps identified. Minor gaps include..."]

SECTION 3 – Experience Breakdown:
Years of Experience: [Extract exact number, e.g., "9 years" or "5-6 years"]
Seniority Level: [ENTRY: 0-2yrs | MID: 2-5yrs | SENIOR: 5-10yrs | LEAD: 10-15yrs | EXECUTIVE: 15+yrs]
Core Technical Skills: [List top 10 technical skills from CV]
Leadership Indicators: [List concrete evidence: "Led 5-person team", "Mentored 3 juniors", or "None mentioned"]

FINAL RECOMMENDATION:
[SHORTLIST | BACKUP | REVIEW]
Confidence: [0-100]%
Match Score: [0-100]%

Reason: [2-3 sentences. First: key strength/weakness vs mandatory requirements. Second: specific evidence from profile. Third: why this verdict.]

===== CRITICAL DECISION RULES =====

**NO AUTO-REJECT POLICY** - AI NEVER rejects candidates:
- SHORTLIST: Meets 80%+ requirements, strong match, ready for interview
- BACKUP: Meets 60-79% requirements, decent match, consider if shortlist pool exhausted
- REVIEW: <60% requirements OR unclear CV → HUMAN RECRUITER MUST DECIDE. Use this for borderline cases.

⚠️ You CANNOT reject candidates. When in doubt, use REVIEW.
⚠️ If Confidence <70%, automatically route to REVIEW regardless of match score.

**Evidence Requirement**:
Your reason MUST cite specific examples from CV:
- BAD: "Good technical skills and experience"
- GOOD: "7 years Python/Django experience matching core stack. Led 3 microservices projects with AWS deployment. Missing Kubernetes (nice-to-have) but Docker experience present."

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
        Parse human-readable prose LLM response into structured JSON
        
        Args:
            prose_response: The prose-format LLM response
            anonymized_id: Candidate's anonymized ID
            
        Returns:
            Structured dictionary with extracted fields
        """
        try:
            # Extract verdict
            verdict_match = re.search(r'FINAL RECOMMENDATION:\s*\n\[(SHORTLIST|BACKUP|REVIEW)\]', prose_response, re.IGNORECASE)
            verdict = verdict_match.group(1).upper() if verdict_match else "REVIEW"
            
            # Extract confidence score
            confidence_match = re.search(r'Confidence:\s*(\d+)%', prose_response)
            confidence_score = int(confidence_match.group(1)) if confidence_match else 50
            
            # Extract match score
            match_match = re.search(r'Match Score:\s*(\d+)%', prose_response)
            match_score = int(match_match.group(1)) if match_match else 50
            
            # Extract verdict reason (text after "Reason:" until end or next section)
            reason_match = re.search(r'Reason:\s*(.+?)(?:\n\n|$)', prose_response, re.DOTALL)
            verdict_reason = reason_match.group(1).strip() if reason_match else "See detailed analysis above"
            
            # Extract years of experience
            years_match = re.search(r'Years of Experience:\s*([0-9.]+(?:-[0-9.]+)?)\s*(?:years?)?', prose_response, re.IGNORECASE)
            if years_match:
                years_str = years_match.group(1)
                if '-' in years_str:
                    # Range like "5-6"
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
            seniority_match = re.search(r'Seniority Level:\s*(ENTRY|MID|SENIOR|LEAD|EXECUTIVE)', prose_response, re.IGNORECASE)
            seniority_level = seniority_match.group(1).upper() if seniority_match else "MID"
            
            # Extract core technical skills (look for list after "Core Technical Skills:")
            skills_section = re.search(r'Core Technical Skills:\s*\[(.+?)\]', prose_response, re.DOTALL)
            if skills_section:
                skills_text = skills_section.group(1)
                core_technical_skills = [s.strip().strip('"\'') for s in skills_text.split(',')]
            else:
                core_technical_skills = []
            
            # Extract leadership indicators
            leadership_section = re.search(r'Leadership Indicators:\s*\[(.+?)\]', prose_response, re.DOTALL)
            if leadership_section:
                leadership_text = leadership_section.group(1)
                leadership_indicators = [s.strip().strip('"\'') for s in leadership_text.split(',')]
            else:
                leadership_indicators = []
            
            # Extract SECTION 1 (General Resume Assessment)
            section1_match = re.search(r'SECTION 1[^\n]*\n(.+?)(?=SECTION 2|FINAL RECOMMENDATION|$)', prose_response, re.DOTALL)
            cleaned_narrative = section1_match.group(1).strip() if section1_match else ""
            
            # Extract matched/missing requirements from SECTION 2
            matched_requirements = []
            missing_requirements = []
            
            # Find Mandatory Skills section
            mandatory_section = re.search(r'Mandatory Skills:(.+?)(?:Secondary Skills:|Gap Analysis:|SECTION 3|$)', prose_response, re.DOTALL)
            if mandatory_section:
                mandatory_text = mandatory_section.group(1)
                # Parse lines like "- Python: Matched — 9 years experience"
                for line in mandatory_text.split('\n'):
                    if 'Matched' in line or 'matched' in line:
                        skill_match = re.search(r'-\s*([^:]+):', line)
                        if skill_match:
                            matched_requirements.append(skill_match.group(1).strip())
                    elif 'Not found' in line or 'not found' in line or 'missing' in line.lower():
                        skill_match = re.search(r'-\s*([^:]+):', line)
                        if skill_match:
                            missing_requirements.append(skill_match.group(1).strip())
            
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
                "leadership_indicators": leadership_indicators,
                
                # Analysis
                "cleaned_narrative": cleaned_narrative,
                "matched_requirements": matched_requirements,
                "missing_requirements": missing_requirements,
                
                # Full prose output for recruiter review
                "detailed_analysis": prose_response
            }
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error parsing prose response: {e}")
            # Return minimal structure with full prose
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
        Extract structured intelligence from a CV with deep analysis and audit trail
        
        Args:
            cv_text: Anonymized CV content
            job_description: Job description to match against
            original_filename: Original filename (for backend tracking only)
            
        Returns:
            Dictionary with structured CV intelligence + full audit trail
        """
        try:
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
                
                # Add metadata
                intelligence["original_filename"] = original_filename or "unknown"
                intelligence["llm_provider"] = self.api_provider
                intelligence["llm_model"] = self.model
                intelligence["extraction_timestamp"] = datetime.now().isoformat()
                intelligence["job_description_hash"] = self._hash_job_description(job_description)
                
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
                                redacted_filename=Path(cv_file).name
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
