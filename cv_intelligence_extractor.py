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
        Create a strict JSON extraction prompt for deep LLM analysis
        
        Args:
            cv_text: Anonymized CV content
            job_description: Job description to match against
            anonymized_id: The generated anonymized candidate ID
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a professional recruiter AI performing DEEP analysis of an anonymized CV against a job description.

===== JOB DESCRIPTION =====
{job_description}

===== ANONYMIZED CV =====
{cv_text}

===== YOUR TASK =====
Extract structured intelligence and provide evidence-based analysis. Respond with ONLY valid JSON (no explanations, no markdown, no code blocks).

{{
  "anonymized_id": "{anonymized_id}",
  "analysis_date": "{datetime.now().isoformat()}",
  
  "cleaned_text": "Complete CV content with no PII, formatted as single paragraph for vector search",
  "cleaned_narrative": "Concise 2-3 sentence professional summary highlighting key strengths and experience",
  
  "years_experience": 5.5,
  "years_experience_range": "5-6",
  "seniority_level": "ENTRY|MID|SENIOR|LEAD|EXECUTIVE",
  
  "core_technical_skills": ["Top 10 most important technical skills"],
  "secondary_technical_skills": ["Additional technical skills beyond core"],
  "frameworks_tools": ["Frameworks, tools, libraries, platforms"],
  "soft_skills": ["Leadership, communication, problem-solving, etc."],
  "certifications": ["Professional certifications, if any"],
  
  "primary_domain": "Main industry/sector",
  "secondary_domains": ["Other domains with experience"],
  "role_types": ["Developer, Engineer, Lead, Manager, Architect, etc."],
  "leadership_indicators": ["Team size led", "Mentoring", "Hiring", "Strategic planning", etc.],
  
  "highest_degree": "Degree name or null",
  "field_of_study": "Field name or null",
  "education_level": "HIGH_SCHOOL|BACHELORS|MASTERS|PHD|OTHER",
  
  "verdict": "SHORTLIST|BACKUP|REVIEW",
  "confidence_score": 85,
  "match_score": 75,
  "verdict_reason": "2-sentence evidence-based explanation. BE SPECIFIC with examples from CV.",
  
  "matched_requirements": ["Specific JD requirements this candidate CLEARLY meets"],
  "missing_requirements": ["Specific JD requirements NOT found in CV"],
  "key_strengths": ["Top 5 strengths relevant to THIS role"],
  "potential_concerns": ["Red flags, gaps, or areas needing verification"],
  
  "search_keywords": ["Important keywords for search/filtering"],
  "highlight_achievements": ["Notable projects, achievements, impact metrics"]
}}

===== CRITICAL INSTRUCTIONS =====

1. **years_experience**: Extract exact decimal (e.g., 5.5) from CV. If range, use midpoint.
2. **seniority_level**: 
   - ENTRY: 0-2 years
   - MID: 2-5 years
   - SENIOR: 5-10 years
   - LEAD: 10-15 years, team leadership
   - EXECUTIVE: 15+ years, strategic leadership
3. **core_technical_skills**: List ONLY the 10 most critical skills for THIS job. Prioritize by JD match + candidate expertise.
4. **verdict - NO AUTO-REJECT POLICY**: 
   - SHORTLIST: Meets 80%+ requirements, strong match, ready for interview
   - BACKUP: Meets 60-79% requirements, decent match, consider if shortlist exhausted  
   - REVIEW: <60% requirements OR unclear CV → HUMAN RECRUITER MUST REVIEW. AI never rejects.
   
   ⚠️ CRITICAL: You CANNOT reject candidates. Use REVIEW for borderline/unclear cases.
   ⚠️ Recruiters review top 50 candidates even if score is low.
   
5. **confidence_score**: Your confidence in the verdict (0-100). Lower if CV is vague or incomplete.
   ⚠️ If confidence <70%, candidate routes to human review immediately.
6. **match_score**: How well candidate fits THIS specific JD (0-100). Be objective.
7. **verdict_reason**: MUST cite specific examples from CV. NO generic statements.
8. **cleaned_text**: Extract full CV content, remove any PII remnants, format as flowing text for vector search.
9. **leadership_indicators**: Extract CONCRETE evidence (team sizes, "led 5 engineers", "hired 3 developers", "mentored juniors")

===== EVIDENCE REQUIREMENT =====
Your verdict_reason MUST reference:
- Specific skills from CV
- Years of experience with key technologies
- Relevant project types or domains
- Concrete achievements or impacts

BAD: "Good technical skills and experience"
GOOD: "7 years Python/AWS expertise matching core requirements. Led 3 microservices projects. Missing Kubernetes experience (nice-to-have)."

===== OUTPUT FORMAT =====
Return ONLY the JSON object. No markdown, no code blocks, no explanations before or after."""
        
        return prompt
    
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
            
            # Parse JSON response
            try:
                # Clean response (remove markdown code blocks if present)
                response = raw_llm_response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()
                
                intelligence = json.loads(response)
                
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
                
                # Ensure anonymized_id is set
                if "anonymized_id" not in intelligence or not intelligence["anonymized_id"]:
                    intelligence["anonymized_id"] = anonymized_id
                
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
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {raw_llm_response[:500]}...")
                
                # Return error structure with audit trail
                return {
                    "error": "JSON_PARSE_ERROR",
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
