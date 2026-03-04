"""
LLM Batch Processor for Anonymized CVs
Processes all redacted CVs and extracts structured metadata using LLM
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import argparse


class QuotaExhaustedException(Exception):
    """Raised when the daily free-tier quota is exhausted (429 after all retries)"""
    pass


class LLMBatchProcessor:
    """Process multiple CVs through LLM for metadata extraction and JD matching"""
    
    def __init__(self, 
                 api_provider: str = "ollama",
                 model: str = None,
                 api_key: str = None,
                 output_dir: str = "llm_analysis"):
        """
        Initialize the batch processor
        
        Args:
            api_provider: 'openai', 'anthropic', 'gemini', or 'ollama' (default: ollama - FREE!)
            model: Model name (default: gpt-4o for OpenAI, claude-3-5-sonnet-20241022 for Anthropic, gemini-2.0-flash for Gemini, qwen2.5:7b for Ollama)
            api_key: API key (reads from env if not provided, not needed for Ollama)
            output_dir: Directory to save results
        """
        self.api_provider = api_provider.lower()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set default models
        if model is None:
            if self.api_provider == "openai":
                self.model = "gpt-4o"
            elif self.api_provider == "anthropic":
                self.model = "claude-3-5-sonnet-20241022"
            elif self.api_provider == "gemini":
                # Allow environment override, default to 1.5-flash if requested, else 2.0-flash
                self.model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
            elif self.api_provider == "ollama":
                self.model = os.getenv("LLM_MODEL", "qwen2.5:7b")  # Allow override
            else:
                raise ValueError(f"Unsupported provider: {api_provider}")
        else:
            self.model = model
        
        # Initialize API client
        if self.api_provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        elif self.api_provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        elif self.api_provider == "gemini":
            from google import genai
            from google.genai import types
            self.client = genai.Client(api_key=api_key or os.getenv("GOOGLE_API_KEY"))
        elif self.api_provider == "ollama":
            import ollama
            self.client = ollama  # Ollama uses module-level functions
        
        self.prompt_template = self._get_prompt_template()
    
    def _get_prompt_template(self) -> str:
        """Get the LLM prompt template"""
        return """You are a senior technical recruiter at a top-tier firm. Analyze the anonymized professional profile below and output **STRICT VALID JSON ONLY** — no other text, no markdown, no prefixes, no apologies.

## OUTPUT SCHEMA (MUST BE VALID JSON)
{{
  "metadata": {{
    "total_years_experience": integer,
    "relevant_years_experience": integer,
    "core_technical_skills": ["skill1", "skill2", ...],
    "tools_and_frameworks": ["tool1", "tool2", ...],
    "industries": ["industry1", ...],
    "seniority_level": "Junior/Mid/Senior/Lead/Principal",
    "has_team_leadership": boolean,
    "domain_expertise": ["domain1", ...]
  }},
  "cleaned_narrative": "2-3 paragraphs of PURE professional content: key projects, technical achievements, measurable impact. NO dates, NO locations, NO education names, NO PII. Example: 'Architected real-time data pipeline using Kafka reducing latency by 40%. Led migration of 15 microservices to Kubernetes...'",
  "jd_fitment": {{
    "mandatory_requirements_met": ["requirement1", ...],
    "mandatory_requirements_missing": ["requirement2", ...],
    "nice_to_have_skills_present": ["skill1", ...],
    "confidence_score": integer
  }},
  "verdict": "SHORTLIST | BACKUP | REJECT",
  "reason": "2 sentences MAX. Sentence 1: Key strength/weakness vs JD mandatory requirements. Sentence 2: Specific evidence from profile. Example: 'Meets all mandatory C++/Android NDK requirements. Led JNI optimization reducing frame drops by 40% in camera pipeline.'"
}}

## CRITICAL RULES
- ⚠️ PII SAFETY: DOUBLE-CHECK output for ANY names/emails/phones/addresses/institution names/URLs. If found, REMOVE IMMEDIATELY. Input is anonymized — output MUST stay anonymized.
- 🚫 NEVER invent skills/experience not explicitly stated in the profile
- 📏 Experience calculation: Count only explicit role durations (e.g., "5 years at Company X"). If unclear, estimate conservatively.
- 🎯 confidence_score logic:
    • 90-100 = SHORTLIST (all mandatory requirements met + strong evidence)
    • 70-89 = BACKUP (minor gaps in mandatory requirements OR weak evidence)
    • 0-69 = REJECT (missing ≥1 mandatory requirement)
- ❓ If JD is missing or empty: set jd_fitment to null and verdict to "PENDING JD"

## JOB DESCRIPTION (MANDATORY REQUIREMENTS IN BOLD)
{job_description}

## ANONYMIZED PROFESSIONAL PROFILE (PII ALREADY REMOVED)
{resume_text}"""
    
    def process_single_cv(self, 
                          cv_text: str, 
                          cv_filename: str,
                          job_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single CV through the LLM
        
        Args:
            cv_text: The resume text content
            cv_filename: Original filename for tracking
            job_description: Optional job description for matching
            
        Returns:
            Dict containing the LLM response and metadata
        """
        # Prepare the prompt
        jd_text = job_description if job_description else "NO JD PROVIDED - Skip JD matching"
        prompt = self.prompt_template.format(
            job_description=jd_text,
            resume_text=cv_text
        )
        
        print(f"  📤 Sending to {self.api_provider.upper()} ({self.model})...")
        
        try:
            # Call the appropriate API
            if self.api_provider == "openai":
                response = self._call_openai(prompt)
            elif self.api_provider == "anthropic":
                response = self._call_anthropic(prompt)
            elif self.api_provider == "gemini":
                response = self._call_gemini(prompt)
            elif self.api_provider == "ollama":
                response = self._call_ollama(prompt)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                result["_meta"] = {
                    "source_file": cv_filename,
                    "processed_at": datetime.now().isoformat(),
                    "model": self.model,
                    "provider": self.api_provider
                }
                print(f"  ✅ Success! Verdict: {result.get('verdict', 'N/A')}")
                return result
            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON parse error: {e}")
                return {
                    "error": "JSON_PARSE_ERROR",
                    "raw_response": response,
                    "_meta": {
                        "source_file": cv_filename,
                        "processed_at": datetime.now().isoformat(),
                        "error": str(e)
                    }
                }
        
        except Exception as e:
            print(f"  ❌ API Error: {e}")
            return {
                "error": "API_ERROR",
                "error_message": str(e),
                "_meta": {
                    "source_file": cv_filename,
                    "processed_at": datetime.now().isoformat()
                }
            }
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a technical recruiter assistant. Always output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API with retry + exponential backoff for rate limits.
        Raises QuotaExhaustedException immediately if daily quota or limit: 0 detected."""
        from google.genai import types
        import logging
        _log = logging.getLogger(__name__)
        
        max_retries = 3
        base_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=8192
                    )
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    # Abort IMMEDIATELY if limit is 0 (account-level block)
                    if 'limit: 0' in error_str:
                        _log.error("API quota limit is 0 — account fully throttled. Aborting immediately.")
                        raise QuotaExhaustedException(
                            "API quota is 0. Your Google account is fully throttled. "
                            "Wait until midnight PT for reset, enable billing, or use a different Google account."
                        )
                    # Abort after 1 retry if daily quota hit
                    is_daily = 'PerDay' in error_str or 'per day' in error_str.lower()
                    if is_daily:
                        _log.error("Daily free-tier quota exhausted. Aborting.")
                        raise QuotaExhaustedException(
                            "Daily free-tier quota exhausted for this API key. "
                            "Wait until quota resets (midnight PT) or upgrade to a paid plan."
                        )
                    # Transient rate limit — retry with backoff
                    delay = base_delay * (2 ** attempt)  # 5, 10, 20 seconds
                    _log.warning(
                        f"Rate limited (429). Retry {attempt+1}/{max_retries} in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    raise
        
        raise QuotaExhaustedException(
            f"Gemini API rate limit exceeded after {max_retries} retries. "
            f"Your free-tier quota may be exhausted. Wait for reset or upgrade plan."
        )
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama (local LLM)"""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior technical recruiter assistant. Analyze CVs thoroughly and follow the output format exactly as specified in the prompt."},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 8192
                }
            )
            return response['message']['content']
        except Exception as e:
            if "connection" in str(e).lower():
                raise Exception(
                    "Cannot connect to Ollama. Please make sure Ollama is running.\n"
                    "1. Download from: https://ollama.com/download\n"
                    f"2. Run: ollama pull {self.model}\n"
                    "3. Ollama will start automatically"
                )
            raise
    
    def generate_analysis(self, prompt: str) -> str:
        """
        Generate analysis from a prompt using the configured LLM
        
        Args:
            prompt: The complete prompt to send to the LLM
            
        Returns:
            Raw string response from the LLM
        """
        if self.api_provider == "openai":
            return self._call_openai(prompt)
        elif self.api_provider == "anthropic":
            return self._call_anthropic(prompt)
        elif self.api_provider == "gemini":
            return self._call_gemini(prompt)
        elif self.api_provider == "ollama":
            return self._call_ollama(prompt)
        else:
            raise ValueError(f"Unsupported API provider: {self.api_provider}")
    
    def process_directory(self, 
                         cv_directory: str,
                         job_description: Optional[str] = None,
                         limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Process all CVs in a directory
        
        Args:
            cv_directory: Path to directory containing CVs
            job_description: Optional job description for matching
            limit: Optional limit on number of CVs to process
            
        Returns:
            Dict with summary statistics and results path
        """
        cv_dir = Path(cv_directory)
        if not cv_dir.exists():
            raise FileNotFoundError(f"Directory not found: {cv_directory}")
        
        # Find all text files
        cv_files = list(cv_dir.glob("*.txt"))
        if limit:
            cv_files = cv_files[:limit]
        
        print(f"\n🔍 Found {len(cv_files)} CV files to process")
        print(f"📋 Using: {self.api_provider.upper()} - {self.model}")
        print(f"💾 Output directory: {self.output_dir}\n")
        
        results = []
        stats = {
            "total": len(cv_files),
            "success": 0,
            "errors": 0,
            "verdicts": {"SHORTLIST": 0, "BACKUP": 0, "REJECT": 0, "PENDING JD": 0}
        }
        
        # Process each CV
        for idx, cv_file in enumerate(cv_files, 1):
            print(f"[{idx}/{len(cv_files)}] Processing: {cv_file.name}")
            
            try:
                # Check if output already exists to avoid re-processing
                intelligence_file = f"{cv_file.stem}_intelligence.json"
                intelligence_path = self.output_dir / intelligence_file
                
                if intelligence_file in existing_files:
                    print(f"  ⏭️  Skipping {cv_file.name} (Already analyzed)")
                    # Load existing for results
                    try:
                        with open(intelligence_path, 'r', encoding='utf-8') as f:
                            results.append(json.load(f))
                    except:
                        pass # If read fails, ignore
                    continue

                # Read CV content
                with open(cv_file, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
                
                # Update stats
                if "error" not in result:
                    stats["success"] += 1
                    verdict = result.get("verdict", "UNKNOWN")
                    stats["verdicts"][verdict] = stats["verdicts"].get(verdict, 0) + 1
                else:
                    stats["errors"] += 1
                
                # Small delay to avoid rate limits
                time.sleep(0.5)
            
            except Exception as e:
                print(f"  ❌ Error reading file: {e}")
                stats["errors"] += 1
                results.append({
                    "error": "FILE_READ_ERROR",
                    "error_message": str(e),
                    "_meta": {"source_file": cv_file.name}
                })
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"batch_results_{timestamp}.json"
        
        output_data = {
            "summary": stats,
            "job_description": job_description,
            "processed_at": datetime.now().isoformat(),
            "model": self.model,
            "provider": self.api_provider,
            "results": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✅ BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total Processed: {stats['total']}")
        print(f"Success: {stats['success']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nVerdicts:")
        for verdict, count in stats['verdicts'].items():
            if count > 0:
                print(f"  {verdict}: {count}")
        print(f"\n💾 Results saved to: {output_file}")
        
        # Generate summary report
        self._generate_summary_report(output_data, timestamp)
        
        return {"stats": stats, "output_file": str(output_file)}
    
    def _generate_summary_report(self, data: Dict, timestamp: str):
        """Generate a human-readable summary report"""
        report_file = self.output_dir / f"summary_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("CV BATCH PROCESSING SUMMARY REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Processed: {data['processed_at']}\n")
            f.write(f"Model: {data['provider'].upper()} - {data['model']}\n")
            f.write(f"Total CVs: {data['summary']['total']}\n")
            f.write(f"Success: {data['summary']['success']}\n")
            f.write(f"Errors: {data['summary']['errors']}\n\n")
            
            if data.get('job_description'):
                f.write("Job Description Provided: YES\n\n")
            else:
                f.write("Job Description Provided: NO\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("VERDICT BREAKDOWN\n")
            f.write("-" * 80 + "\n")
            for verdict, count in data['summary']['verdicts'].items():
                if count > 0:
                    f.write(f"{verdict}: {count}\n")
            
            # Detailed results
            f.write("\n" + "-" * 80 + "\n")
            f.write("DETAILED RESULTS\n")
            f.write("-" * 80 + "\n\n")
            
            for idx, result in enumerate(data['results'], 1):
                filename = result.get('_meta', {}).get('source_file', 'Unknown')
                f.write(f"{idx}. {filename}\n")
                
                if 'error' in result:
                    f.write(f"   Status: ERROR - {result['error']}\n")
                else:
                    verdict = result.get('verdict', 'N/A')
                    confidence = result.get('jd_fitment', {}).get('confidence_score', 'N/A')
                    f.write(f"   Verdict: {verdict}\n")
                    f.write(f"   Confidence: {confidence}\n")
                    f.write(f"   Experience: {result.get('metadata', {}).get('total_years_experience', 'N/A')} years\n")
                    f.write(f"   Seniority: {result.get('metadata', {}).get('seniority_level', 'N/A')}\n")
                    f.write(f"   Reason: {result.get('reason', 'N/A')}\n")
                f.write("\n")
        
        print(f"📄 Summary report: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch process CVs through LLM for metadata extraction and JD matching"
    )
    parser.add_argument(
        "cv_directory",
        help="Directory containing redacted CV files (default: final_output/)",
        nargs='?',
        default="final_output"
    )
    parser.add_argument(
        "--jd",
        help="Path to job description file (optional)",
        default=None
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "gemini", "ollama"],
        default="ollama",
        help="LLM provider to use (default: ollama - free and local!)"
    )
    parser.add_argument(
        "--model",
        help="Model name (default: gpt-4o for OpenAI, claude-3-5-sonnet-20241022 for Anthropic, gemini-2.0-flash for Gemini, qwen2.5:7b for Ollama)",
        default=None
    )
    parser.add_argument(
        "--api-key",
        help="API key (reads from env if not provided)",
        default=None
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for results (default: llm_analysis)",
        default="llm_analysis"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of CVs to process (for testing)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Read job description if provided
    job_description = None
    if args.jd:
        jd_path = Path(args.jd)
        if jd_path.exists():
            with open(jd_path, 'r', encoding='utf-8') as f:
                job_description = f.read()
            print(f"📋 Loaded job description from: {args.jd}")
        else:
            print(f"⚠️ Job description file not found: {args.jd}")
            return
    
    # Initialize processor
    try:
        processor = LLMBatchProcessor(
            api_provider=args.provider,
            model=args.model,
            api_key=args.api_key,
            output_dir=args.output_dir
        )
        
        # Process directory
        processor.process_directory(
            cv_directory=args.cv_directory,
            job_description=job_description,
            limit=args.limit
        )
    
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        print("\nTroubleshooting:")
        print("1. For Ollama (FREE - Recommended):")
        print("   - Download: https://ollama.com/download")
        print("   - Run: ollama pull qwen2.5:7b")
        print("   - Then retry this command")
        print("\n2. Or set API key for cloud providers:")
        print("   - OpenAI: set OPENAI_API_KEY=your-key")
        print("   - Anthropic: set ANTHROPIC_API_KEY=your-key")
        print("   - Gemini: set GOOGLE_API_KEY=your-key")
        print("\n3. Install packages: pip install openai anthropic google-genai ollama")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
