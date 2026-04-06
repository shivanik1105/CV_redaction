# CV Processing Modes

The system now supports two processing modes:

## 1. Extraction-Only Mode (No JD Required)

Process CVs to extract skills, experience, and professional information WITHOUT matching against a job description.

### Usage:
```bash
python process_all_cvs_smart.py --max 10
```

### What it does:
- Redacts PII from CVs
- Extracts structured information:
  - Years of experience
  - Core technical skills
  - Secondary skills
  - Primary domain/industry
  - Seniority level
  - Leadership indicators
  - Professional summary
- Stores in database with `verdict=None`, `match_score=None`
- No job matching performed

### Use cases:
- Building a talent pool/database
- Initial CV screening before defining job requirements
- Cataloging candidate profiles for future opportunities
- Skills inventory management

---

## 2. JD Matching Mode (With Job Description)

Process CVs and match them against a specific job description.

### Usage:
```bash
python process_all_cvs_smart.py --jd "Senior Python Developer with 5+ years experience..." --max 10
```

### What it does:
- Everything from Extraction-Only mode, PLUS:
- Compares candidate profile against JD requirements
- Generates match score (0-100%)
- Provides verdict: SHORTLIST, BACKUP, or REVIEW
- Identifies matched/missing requirements
- Detailed fitment analysis by category

### Use cases:
- Active recruitment for specific roles
- Ranking candidates for a position
- Identifying best-fit candidates
- Automated pre-screening

---

## Database Fields

### Common fields (both modes):
- `anonymized_id`: Unique candidate ID (e.g., CAND_882)
- `years_experience`: Total years of experience
- `core_technical_skills`: Array of primary skills
- `secondary_technical_skills`: Array of additional skills
- `primary_domain`: Main industry/sector
- `seniority_level`: ENTRY/MID/SENIOR/LEAD/EXECUTIVE
- `leadership_indicators`: Array of leadership evidence
- `confidence_score`: LLM confidence in extraction (0-100%)

### JD Matching fields (only when JD provided):
- `verdict`: SHORTLIST/BACKUP/REVIEW
- `match_score`: How well CV matches JD (0-100%)
- `matched_requirements`: Array of met requirements
- `missing_requirements`: Array of gaps
- `fitment_analysis`: Detailed category-by-category comparison

### Mode indicator:
- `has_jd_matching`: Boolean flag (true if JD was provided)
- `job_description_hash`: Hash of JD used (null if no JD)

---

## Examples

### Extract all CVs without JD:
```bash
python process_all_cvs_smart.py --max 100
```

### Match CVs against a specific role:
```bash
python process_all_cvs_smart.py --jd "We need a Senior Java Developer with Spring Boot, Microservices, and AWS experience. 8+ years required." --max 50
```

### Process just 5 CVs for testing:
```bash
python process_all_cvs_smart.py --max 5
```

---

## Cost Implications

- Groq API is FREE (6,000 requests/day)
- Extraction-only mode uses ~same tokens as matching mode
- No cost difference between modes
- Both modes store in Supabase database

---

## Migration Notes

If you have existing CVs processed with a generic JD, you can:
1. Keep them as-is (they have match scores)
2. Re-process without JD to get pure extraction data
3. Re-process with a real JD when you have a specific role

The system handles both types of records in the database.
