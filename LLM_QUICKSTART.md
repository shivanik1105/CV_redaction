# LLM CV Analysis - Quick Start

## Installation (2 minutes)

```bash
# 1. Install LLM dependencies
pip install openai anthropic google-genai

# 2. Set API key (choose one)
set OPENAI_API_KEY=sk-your-openai-key-here
# OR
set ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
# OR
set GOOGLE_API_KEY=your-google-api-key-here

# 3. Test installation
python llm_batch_processor.py --limit 1
```

## Basic Usage

### Analyze All CVs (No Job Description)
```bash
python llm_batch_processor.py
```
**Output:** Extracts metadata (skills, experience, seniority) but no JD matching

### Analyze with Job Description Matching
```bash
python llm_batch_processor.py --jd example_job_description.txt
```
**Output:** Full analysis with SHORTLIST/BACKUP/REJECT verdicts

### Analyze Single CV
```bash
python single_cv_analyzer.py "final_output/REDACTED_CV Jonny Kanwar.txt" example_job_description.txt
```
**Output:** Pretty-printed analysis for one CV

### Complete Automated Pipeline
```powershell
.\analyze_resumes.ps1 -JobDescription example_job_description.txt
```
**Does:** 
1. Redacts all CVs from `resume/` → `final_output/`
2. Analyzes with LLM
3. Shows summary and opens results

## Example Results

### Console Output
```
🔍 Found 50 CV files to process
📋 Using: OPENAI - gpt-4o

[1/50] Processing: REDACTED_CV Jonny Kanwar.txt
  📤 Sending to OPENAI (gpt-4o)...
  ✅ Success! Verdict: SHORTLIST

...

✅ BATCH PROCESSING COMPLETE
============================================================
Total Processed: 50
Success: 50
Errors: 0

Verdicts:
  SHORTLIST: 12
  BACKUP: 20
  REJECT: 18

💾 Results saved to: llm_analysis/batch_results_20260209_103000.json
📄 Summary report: llm_analysis/summary_report_20260209_103000.txt
```

### JSON Output Structure
```json
{
  "summary": {
    "total": 50,
    "success": 50,
    "errors": 0,
    "verdicts": {
      "SHORTLIST": 12,
      "BACKUP": 20,
      "REJECT": 18
    }
  },
  "results": [
    {
      "metadata": {
        "total_years_experience": 12,
        "relevant_years_experience": 12,
        "core_technical_skills": ["AUTOSAR", "Embedded C", "C++", "ISO 26262"],
        "tools_and_frameworks": ["Vector CANoe", "Eclipse", "Infineon Aurix"],
        "seniority_level": "Senior",
        "has_team_leadership": true,
        "domain_expertise": ["Automotive Embedded Systems", "Electric Powertrain"]
      },
      "cleaned_narrative": "Senior automotive embedded software engineer with 12 years...",
      "jd_fitment": {
        "mandatory_requirements_met": ["5+ years AUTOSAR", "Embedded C/C++", "ISO 26262"],
        "mandatory_requirements_missing": [],
        "nice_to_have_skills_present": ["Cybersecurity", "Electric Vehicle"],
        "confidence_score": 95
      },
      "verdict": "SHORTLIST",
      "reason": "Meets all mandatory requirements with 12 years AUTOSAR experience. Led electric powertrain projects for major OEMs.",
      "_meta": {
        "source_file": "REDACTED_CV Jonny Kanwar.txt",
        "processed_at": "2026-02-09T10:30:00",
        "model": "gpt-4o"
      }
    }
  ]
}
```

## Common Commands

```bash
# Test with 3 CVs first
python llm_batch_processor.py --limit 3

# Use cheaper/faster model
python llm_batch_processor.py --model gpt-4o-mini

# Use Anthropic Claude instead
python llm_batch_processor.py --provider anthropic

# Use Google Gemini
python llm_batch_processor.py --provider gemini

# Process specific directory
python llm_batch_processor.py path/to/cvs/ --jd job.txt

# Specify output directory
python llm_batch_processor.py --output-dir my_results
```

## Creating Job Descriptions

Create a text file with mandatory requirements in BOLD or clearly marked:

```text
Senior Backend Engineer

MANDATORY REQUIREMENTS (Must Have):
• 5+ years Python development
• Django or Flask experience
• PostgreSQL database design
• REST API development
• Docker containerization

NICE TO HAVE (Preferred):
• AWS/Azure cloud experience
• Kubernetes orchestration
• Redis caching
• CI/CD pipeline setup

We're seeking an experienced backend engineer to build scalable APIs...
```

Save as `backend_engineer_jd.txt` and run:
```bash
python llm_batch_processor.py --jd backend_engineer_jd.txt
```

## Troubleshooting

### "API key not found"
```bash
# Check if set
echo %OPENAI_API_KEY%

# Set it
set OPENAI_API_KEY=sk-...
```

### "Module not found: openai"
```bash
pip install openai anthropic
```

### Rate Limits
- OpenAI Tier 1: 500 requests/day
- Built-in 0.5s delay between requests
- Use `--limit` to test with fewer CVs first

### JSON Parse Errors
- Rare, automatically logged in results
- Check `error` field in output JSON
- Processing continues for other CVs

## Next Steps

1. ✅ Test: `python llm_batch_processor.py --limit 3`
2. ✅ Create your job description file
3. ✅ Run full batch: `python llm_batch_processor.py --jd yourjob.txt`
4. ✅ Review results in `llm_analysis/` folder
5. ✅ Filter SHORTLIST candidates for interviews

📖 Full documentation: [LLM_ANALYSIS_README.md](LLM_ANALYSIS_README.md)
