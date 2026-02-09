# LLM CV Analysis - Complete Guide

## Overview
Analyze anonymized CVs using LLM for structured metadata extraction, JD matching, and candidate scoring.

## Quick Start

### 1. Install Dependencies
```bash
pip install openai anthropic google-genai
```

### 2. Set API Key
```bash
# For OpenAI (recommended)
set OPENAI_API_KEY=your-api-key-here

# OR for Anthropic
set ANTHROPIC_API_KEY=your-api-key-here

# OR for Google Gemini
set GOOGLE_API_KEY=your-api-key-here
```

### 3. Process All CVs in final_output/
```bash
# Basic usage (no JD matching)
python llm_batch_processor.py

# With job description
python llm_batch_processor.py --jd job_description.txt

# Process only first 5 CVs (testing)
python llm_batch_processor.py --limit 5

# Use Anthropic Claude instead of OpenAI
python llm_batch_processor.py --provider anthropic

# Use Google Gemini
python llm_batch_processor.py --provider gemini
```

## Usage Examples

### Example 1: Analyze without Job Description
```bash
python llm_batch_processor.py final_output/
```
**Output:**
- `llm_analysis/batch_results_TIMESTAMP.json` - Full JSON results
- `llm_analysis/summary_report_TIMESTAMP.txt` - Human-readable report
- All CVs get verdict "PENDING JD"

### Example 2: Screen Candidates for Specific Role
```bash
# Create job description file
echo "Senior Automotive Embedded Software Engineer. MANDATORY: 5+ years AUTOSAR, C/C++, ISO 26262, Infineon Aurix. NICE TO HAVE: Cybersecurity, Electric Vehicle experience." > jd_embedded.txt

# Run analysis
python llm_batch_processor.py --jd jd_embedded.txt

# Results will include:
# - SHORTLIST candidates (90-100% match)
# - BACKUP candidates (70-89% match)
# - REJECT candidates (<70% match)
```

### Example 3: Test on Limited CVs
```bash
# Process only 3 CVs for testing
python llm_batch_processor.py --limit 3 --jd myjob.txt
```

### Example 4: Use Different Model
```bash
# Use GPT-4o-mini (cheaper, faster)
python llm_batch_processor.py --model gpt-4o-mini

# Use Claude Sonnet
python llm_batch_processor.py --provider anthropic --model claude-3-5-sonnet-20241022
```

## Output Structure

### JSON Output (batch_results_TIMESTAMP.json)
```json
{
  "summary": {
    "total": 50,
    "success": 48,
    "errors": 2,
    "verdicts": {
      "SHORTLIST": 12,
      "BACKUP": 20,
      "REJECT": 16
    }
  },
  "job_description": "...",
  "results": [
    {
      "metadata": {
        "total_years_experience": 12,
        "relevant_years_experience": 12,
        "core_technical_skills": ["AUTOSAR", "Embedded C", "C++"],
        "tools_and_frameworks": ["Vector CANoe", "Eclipse"],
        "industries": ["Automotive"],
        "seniority_level": "Senior",
        "has_team_leadership": true,
        "domain_expertise": ["Electric Powertrain"]
      },
      "cleaned_narrative": "...",
      "jd_fitment": {
        "mandatory_requirements_met": ["AUTOSAR", "C/C++", "ISO 26262"],
        "mandatory_requirements_missing": [],
        "nice_to_have_skills_present": ["Cybersecurity"],
        "confidence_score": 95
      },
      "verdict": "SHORTLIST",
      "reason": "Meets all mandatory requirements. 12 years AUTOSAR experience with Infineon Aurix.",
      "_meta": {
        "source_file": "REDACTED_CV Jonny Kanwar.txt",
        "processed_at": "2026-02-09T10:30:00",
        "model": "gpt-4o",
        "provider": "openai"
      }
    }
  ]
}
```

### Text Report (summary_report_TIMESTAMP.txt)
```
================================================================================
CV BATCH PROCESSING SUMMARY REPORT
================================================================================

Processed: 2026-02-09T10:30:00
Model: OPENAI - gpt-4o
Total CVs: 50
Success: 48
Errors: 2

VERDICT BREAKDOWN
--------------------------------------------------------------------------------
SHORTLIST: 12
BACKUP: 20
REJECT: 16

DETAILED RESULTS
--------------------------------------------------------------------------------

1. REDACTED_CV Jonny Kanwar.txt
   Verdict: SHORTLIST
   Confidence: 95
   Experience: 12 years
   Seniority: Senior
   Reason: Meets all mandatory requirements. 12 years AUTOSAR experience.

2. REDACTED_CV_Sebastian_Loew_eng.txt
   Verdict: BACKUP
   Confidence: 78
   Experience: 8 years
   Seniority: Mid
   Reason: Missing Infineon Aurix experience. Strong AUTOSAR background.
```

## Integration with Existing Pipeline

### Full Pipeline: Redaction → LLM Analysis
```bash
# Step 1: Redact CVs
python cv_redaction_pipeline.py resume/ final_output/

# Step 2: Analyze with LLM
python llm_batch_processor.py final_output/ --jd job.txt

# Results in llm_analysis/ folder
```

### Automated Combined Script
Create `analyze_resumes.ps1`:
```powershell
# Redact all CVs
Write-Host "Step 1: Redacting CVs..." -ForegroundColor Cyan
python cv_redaction_pipeline.py resume/ final_output/

# Analyze with LLM
Write-Host "Step 2: Analyzing with LLM..." -ForegroundColor Cyan
python llm_batch_processor.py final_output/ --jd job_description.txt

# Open results
Write-Host "Done! Opening results..." -ForegroundColor Green
Get-ChildItem llm_analysis/*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Invoke-Item
```

## Command Reference

### All Options
```bash
python llm_batch_processor.py [cv_directory] [options]

Arguments:
  cv_directory        Directory with CVs (default: final_output/)

Options:
  --jd FILE          Job description file path
  --provider CHOICE  API provider: openai | anthropic | gemini (default: openai)
  --model NAME       Model name (default: gpt-4o | claude-3-5-sonnet-20241022 | gemini-1.5-pro)
  --api-key KEY      API key (or set env variable)
  --output-dir DIR   Output directory (default: llm_analysis)
  --limit N          Process only N CVs (for testing)
```

## Cost Estimation

### OpenAI (gpt-4o)
- **Cost per CV**: ~$0.03 - $0.10 (depending on CV length)
- **50 CVs**: ~$2.50 - $5.00
- **1000 CVs**: ~$50 - $100

### Anthropic (Claude Sonnet)
- **Cost per CV**: ~$0.05 - $0.15
- **50 CVs**: ~$4.00 - $7.50
- **1000 CVs**: ~$80 - $150

### Google Gemini (gemini-1.5-pro)
- **Cost per CV**: ~$0.01 - $0.05 (cheaper!)
- **50 CVs**: ~$1.00 - $2.50
- **1000 CVs**: ~$20 - $50

💡 **Tip**: Use `--limit 5` first to test before processing all CVs.

## Troubleshooting

### Error: "API key not found"
```bash
# Set environment variable
set OPENAI_API_KEY=sk-...
# OR
set ANTHROPIC_API_KEY=sk-ant-...
# OR
set GOOGLE_API_KEY=...
```

### Error: "Module not found: openai"
```bash
pip install openai anthropic google-genai
```

### Rate Limits
The processor includes 0.5s delays between requests. For large batches:
- OpenAI: Tier 1 = 500 requests/day
- Anthropic: Check your account limits

### JSON Parse Errors
Rare, but if LLM returns invalid JSON:
- The error is logged in results
- Check `raw_response` field in output JSON
- No action needed - continue processing

## Advanced Usage

### Python API
```python
from llm_batch_processor import LLMBatchProcessor

# Initialize
processor = LLMBatchProcessor(
    api_provider="openai",
    model="gpt-4o",
    output_dir="my_results"
)

# Process single CV
with open("cv.txt", "r") as f:
    cv_text = f.read()

result = processor.process_single_cv(
    cv_text=cv_text,
    cv_filename="cv.txt",
    job_description="Your JD here"
)

print(result["verdict"])  # SHORTLIST/BACKUP/REJECT

# Process directory
stats = processor.process_directory(
    cv_directory="final_output/",
    job_description="Your JD here",
    limit=10  # Optional
)
```

### Custom Filtering
```python
import json

# Load results
with open("llm_analysis/batch_results_20260209_103000.json", "r") as f:
    data = json.load(f)

# Filter SHORTLIST candidates with 10+ years
shortlist = [
    r for r in data["results"]
    if r.get("verdict") == "SHORTLIST"
    and r.get("metadata", {}).get("total_years_experience", 0) >= 10
]

print(f"Found {len(shortlist)} senior shortlist candidates")
```

## Best Practices

1. **Always redact first**: Run `cv_redaction_pipeline.py` before LLM analysis
2. **Test with --limit**: Process 3-5 CVs first to verify setup
3. **Clear job descriptions**: Be explicit about mandatory vs nice-to-have requirements
4. **Review confidence scores**: 
   - 90-100: High confidence matches
   - 70-89: Review manually
   - <70: Likely not a fit
5. **Check _meta field**: Verify which model processed each CV

## FAQ

**Q: Can I use local LLMs?**  
A: Not currently. Only OpenAI and Anthropic APIs supported.

**Q: Is PII safe?**  
A: Yes! CVs in `final_output/` are already anonymized by your redaction pipeline. The LLM prompt explicitly prevents PII in output.

**Q: What if I don't have a JD?**  
A: Run without `--jd` flag. Results will include metadata extraction but no fitment score.

**Q: Can I process PDFs directly?**  
A: No. Use `cv_redaction_pipeline.py` first to convert and anonymize.

**Q: How to get only SHORTLIST candidates?**  
A: Open the JSON results and filter by `"verdict": "SHORTLIST"`.

## Next Steps

1. ✅ Run test batch: `python llm_batch_processor.py --limit 3`
2. ✅ Create job description file with clear mandatory requirements
3. ✅ Process full directory: `python llm_batch_processor.py --jd myjob.txt`
4. ✅ Review results in `llm_analysis/` folder
5. ✅ Filter shortlisted candidates for interviews
