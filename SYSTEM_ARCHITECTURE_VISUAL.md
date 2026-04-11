# CV Intelligence System - Visual Architecture

## 🎯 Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR CV PROCESSING SYSTEM                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          OPTION 1: NATIVE GUI                            │
│                        (Quick PII Redaction Only)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   📁 dist\CVRedactor.exe (81 MB)                                         │
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │  🖥️  Native Windows GUI (tkinter)                           │      │
│   │                                                               │      │
│   │  1. Browse CV... → Select PDF/DOCX                           │      │
│   │  2. Save As... → Choose output location                      │      │
│   │  3. 🚀 Redact This CV → Process                              │      │
│   │  4. View log → See real-time progress                        │      │
│   │  5. Open file → View redacted CV                             │      │
│   │                                                               │      │
│   │  ✅ Multi-column support (Sunil Durgale CV fixed!)          │      │
│   │  ✅ No browser needed                                         │      │
│   │  ✅ No internet required                                      │      │
│   │  ✅ No Python installation needed                            │      │
│   │  ✅ Processing: 1-2 seconds per CV                           │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                                                           │
│   📤 Output: Anonymized text file (PII removed)                          │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       OPTION 2: WEB APPLICATION                          │
│                    (Full Recruitment Intelligence)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   🚀 Start: python app_launcher.py                                       │
│   🌐 Access: http://localhost:5000                                       │
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │  📄 Page 1: CV Redactor (/redactor)                          │      │
│   │  ├─ Upload CV                                                 │      │
│   │  ├─ Redact PII                                                │      │
│   │  └─ Download anonymized CV                                    │      │
│   │                                                                │      │
│   │  Same as Native GUI but in browser                            │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │  📤 Page 2: Upload & Process (/upload)                       │      │
│   │  ├─ Upload CV (single or batch)                              │      │
│   │  ├─ Redact PII (automatic)                                    │      │
│   │  ├─ Extract Intelligence (LLM)                                │      │
│   │  │   ├─ Skills (core, secondary, frameworks)                 │      │
│   │  │   ├─ Experience (years, seniority)                        │      │
│   │  │   ├─ Domain expertise                                      │      │
│   │  │   └─ Leadership indicators                                 │      │
│   │  ├─ Match with Job Description (optional)                     │      │
│   │  │   ├─ Match score (0-100)                                   │      │
│   │  │   ├─ Verdict (SHORTLIST/BACKUP/REJECT)                    │      │
│   │  │   ├─ Matched requirements                                  │      │
│   │  │   └─ Missing requirements                                  │      │
│   │  └─ Store results                                              │      │
│   │      ├─ Supabase (if configured)                              │      │
│   │      └─ Local JSON (automatic fallback)                       │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │  🔍 Page 3: Search Candidates (/search)                      │      │
│   │  ├─ Quick search (name, skills)                              │      │
│   │  ├─ Advanced filters                                          │      │
│   │  │   ├─ Verdict (SHORTLIST/BACKUP)                           │      │
│   │  │   ├─ Seniority level                                       │      │
│   │  │   ├─ Match score range                                     │      │
│   │  │   ├─ Years of experience                                   │      │
│   │  │   ├─ Required skills                                       │      │
│   │  │   └─ Domain expertise                                      │      │
│   │  └─ View candidate profiles                                   │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                                                           │
│   ┌─────────────────────────────────────────────────────────────┐      │
│   │  📊 Page 4: Dashboard (/dashboard)                           │      │
│   │  ├─ Statistics                                                │      │
│   │  │   ├─ Total candidates                                      │      │
│   │  │   ├─ Shortlisted / Backup / Rejected                      │      │
│   │  │   ├─ Average match score                                   │      │
│   │  │   └─ Average confidence score                              │      │
│   │  ├─ System Health                                             │      │
│   │  │   ├─ LLM Provider status                                   │      │
│   │  │   ├─ Supabase status                                       │      │
│   │  │   └─ Embedding provider status                             │      │
│   │  └─ Data source (Supabase or Local JSON)                     │      │
│   └─────────────────────────────────────────────────────────────┘      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

```
┌─────────────┐
│   Upload    │
│   CV File   │
│ (PDF/DOCX)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 1: CV EXTRACTION                                   │
│  ├─ Detect CV type (Standard/Naukri/Scanned/Creative)  │
│  ├─ Extract text with column detection                  │
│  │   ├─ Single column: Read top to bottom              │
│  │   └─ Multi-column: Detect layout, read properly     │
│  └─ Output: Raw text with proper section sequence       │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2: PII REDACTION                                   │
│  ├─ Detect PII patterns                                  │
│  │   ├─ Names (Presidio + spaCy)                        │
│  │   ├─ Emails (regex)                                   │
│  │   ├─ Phones (regex + phonenumbers)                   │
│  │   └─ Addresses (Presidio)                            │
│  ├─ Replace with placeholders                            │
│  │   ├─ [REDACTED_NAME]                                 │
│  │   ├─ [REDACTED_EMAIL]                                │
│  │   ├─ [REDACTED_PHONE]                                │
│  │   └─ [REDACTED_ADDRESS]                              │
│  └─ Output: Anonymized CV text                           │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────────────────┐
       │                                                   │
       ▼                                                   ▼
┌─────────────────┐                          ┌──────────────────────┐
│  NATIVE GUI     │                          │  WEB APP CONTINUES   │
│  Stops here     │                          │  (if using /upload)  │
│  Save to file   │                          └──────────┬───────────┘
└─────────────────┘                                     │
                                                        ▼
                                    ┌─────────────────────────────────────┐
                                    │  STEP 3: INTELLIGENCE EXTRACTION    │
                                    │  (Optional - requires LLM)          │
                                    │  ├─ Send to LLM (Groq/OpenAI/etc)  │
                                    │  ├─ Extract structured data         │
                                    │  │   ├─ Core technical skills       │
                                    │  │   ├─ Years of experience         │
                                    │  │   ├─ Seniority level             │
                                    │  │   ├─ Domain expertise            │
                                    │  │   ├─ Leadership indicators       │
                                    │  │   └─ Cleaned narrative           │
                                    │  └─ Output: Intelligence JSON       │
                                    └──────┬──────────────────────────────┘
                                           │
                                           ▼
                                    ┌─────────────────────────────────────┐
                                    │  STEP 4: JD MATCHING (Optional)     │
                                    │  ├─ Compare CV with Job Description │
                                    │  ├─ Calculate match score (0-100)   │
                                    │  ├─ Generate verdict                │
                                    │  │   ├─ SHORTLIST (80-100)          │
                                    │  │   ├─ BACKUP (60-79)              │
                                    │  │   └─ REJECT (<60)                │
                                    │  ├─ Identify matched requirements   │
                                    │  └─ Identify missing requirements   │
                                    └──────┬──────────────────────────────┘
                                           │
                                           ▼
                                    ┌─────────────────────────────────────┐
                                    │  STEP 5: STORAGE                    │
                                    │  ├─ Generate embedding (vector)     │
                                    │  ├─ Save to Supabase (if configured)│
                                    │  │   ├─ cv_intelligence table       │
                                    │  │   └─ pgvector for search         │
                                    │  └─ Save to Local JSON (always)     │
                                    │      └─ llm_analysis/*.json         │
                                    └──────┬──────────────────────────────┘
                                           │
                                           ▼
                                    ┌─────────────────────────────────────┐
                                    │  STEP 6: SEARCH & RETRIEVE          │
                                    │  ├─ Quick search (text matching)    │
                                    │  ├─ Advanced filters                │
                                    │  ├─ Semantic search (vector)        │
                                    │  └─ Rank by match score             │
                                    └─────────────────────────────────────┘
```

## 🔧 Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│  universal_pipeline_engine.py                                    │
│  ├─ PipelineOrchestrator (main class)                           │
│  ├─ StandardATSPipeline (multi-column fix here!)               │
│  ├─ NaukriPipeline                                               │
│  ├─ ScannedImagePipeline                                         │
│  └─ CreativeDesignerPipeline                                     │
│                                                                   │
│  ✅ Sunil Durgale CV fix applied here                           │
│  ✅ Used by both Native GUI and Web App                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  cv_intelligence_extractor.py                                    │
│  ├─ CVIntelligenceExtractor (main class)                        │
│  ├─ Supports multiple LLM providers                             │
│  │   ├─ Groq (free tier: 6000 req/day)                         │
│  │   ├─ OpenAI                                                   │
│  │   ├─ Anthropic (Claude)                                       │
│  │   ├─ Google Gemini                                            │
│  │   └─ Ollama (local)                                           │
│  └─ Extracts structured intelligence from redacted CVs           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  supabase_storage.py                                             │
│  ├─ SupabaseStorage (main class)                                │
│  ├─ Stores CV intelligence in cloud                             │
│  ├─ Supports vector search (pgvector)                           │
│  └─ Optional - automatic fallback to local JSON                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  app.py                                                          │
│  ├─ Flask web application                                        │
│  ├─ Routes:                                                       │
│  │   ├─ /redactor (CV redaction only)                          │
│  │   ├─ /upload (full processing)                               │
│  │   ├─ /search (candidate search)                              │
│  │   └─ /dashboard (statistics)                                 │
│  └─ Automatic Supabase/Local fallback                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  cv_redactor_gui.py                                              │
│  ├─ Native Windows GUI (tkinter)                                │
│  ├─ Standalone redaction only                                    │
│  └─ Uses same PipelineOrchestrator as web app                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Sunil Durgale CV - Before & After

### ❌ Before Fix (Mixed Sections):
```
[REDACTED_NAME]  [REDACTED_EMAIL]  [REDACTED_PHONE]

SUMMARY
  [empty or mixed content]

SKILLS
  [empty or mixed content]

WORK EXPERIENCE
  [all content jumbled here including summary and skills]
```

### ✅ After Fix (Proper Sequence):
```
[REDACTED_NAME]  [REDACTED_EMAIL]  [REDACTED_PHONE]  [REDACTED_URL]

SUMMARY
Streamlined CRM management within Growth Squad for optimal efficiency.
Responsible for renewing orders based on subscription.
Customer Success Operations...

SKILLS
Sales forecasting, CRM management, Salesforce, HubSpot, Oracle,
Lightning, Google Docs, Spreadsheets...

WORK EXPERIENCE
Leena AI Pvt. Ltd. - Sales and Revenue Operations Manager
07/2021 - 04/2025
• Streamlined CRM management within Growth Squad...
• Customer Success Operations...
• Sales forecasting...

Rockwell Automation - Sales Operation Analyst
02/2018 - 01/2020
• I worked as a Sales Operations Analyst...
• Use of Hub Spot for creating accounts...

Tata Technologies - Supply Chain Specialist
06/2014 - 01/2018
• Review and ensure appropriate replenishment...
• Creating new orders for the aftermarket...
```

## 🎯 When to Use What

| Scenario | Tool | Reason |
|----------|------|--------|
| Quick PII removal for 1 CV | Native GUI | Fastest, no setup |
| Redact 5-10 CVs | Native GUI | Simple, offline |
| Redact + extract intelligence | Web App /upload | Needs LLM |
| Match CVs with JD | Web App /upload | Needs LLM + JD |
| Search candidates | Web App /search | Needs database |
| Team collaboration | Web App + Supabase | Cloud storage |
| Offline processing | Native GUI or Web App (local) | No internet |
| Production deployment | Web App + Supabase | Scalable |

## 🚀 Quick Start Commands

```powershell
# Native GUI (Standalone)
cd dist\CVRedactor_Package
.\CVRedactor.exe

# Web App (Full System)
python app_launcher.py
# Opens: http://localhost:5000

# Test Sunil Durgale CV
python app_launcher.py --test "samples/Resume -Sunil Durgale.pdf"

# Check system status
# Go to: http://localhost:5000/dashboard
```

## ✅ Summary

- **Sunil Durgale CV**: ✅ Fixed! Multi-column extraction works perfectly
- **Native GUI**: ✅ Built! Standalone .exe ready
- **Web App**: ✅ Working! Full recruitment system
- **Integration**: ✅ Complete! Both use same redaction engine
- **Supabase**: ⚠️ Optional - configure .env or use local mode

Everything is ready to use! 🎉
