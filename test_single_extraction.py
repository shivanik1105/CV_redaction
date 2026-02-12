"""
Test single CV intelligence extraction
"""
from cv_intelligence_extractor import CVIntelligenceExtractor
from supabase_storage import SupabaseStorage
import sys

def test_single_cv():
    print("\n" + "="*60)
    print(" Testing Single CV Intelligence Extraction")
    print("="*60 + "\n")
    
    # Read a redacted CV
    cv_path = "redacted_output/REDACTED_20260211_212544_Naukri_jyotiSaxena9y_1m.pdf.txt"
    
    try:
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
        print(f"✓ Loaded CV: {cv_path}")
        print(f"  Length: {len(cv_text)} characters\n")
    except FileNotFoundError:
        print(f"✗ CV file not found: {cv_path}")
        print("\nAvailable CVs in redacted_output:")
        import os
        for f in os.listdir("redacted_output")[:5]:
            if f.endswith('.txt'):
                print(f"  - {f}")
        sys.exit(1)
    
    # Job description
    job_description = """
Senior Python Developer - 5+ Years Experience

Requirements:
- 5+ years of professional Python development
- Strong experience with Django or Flask frameworks
- Database experience (PostgreSQL, MySQL)
- REST API design and development
- Cloud platforms (AWS, Azure, or GCP)
- Git version control

Nice to have:
- DevOps experience (Docker, Kubernetes)
- CI/CD pipeline knowledge
"""
    
    print("Job Description:")
    print(job_description.strip())
    print("\n" + "-"*60 + "\n")
    
    # Extract intelligence
    print("🤖 Extracting intelligence with Google Gemini...\n")
    
    try:
        extractor = CVIntelligenceExtractor(api_provider="gemini")
        print("✓ Extractor initialized\n")
        
        intelligence = extractor.extract_intelligence(
            cv_text=cv_text,
            job_description=job_description,
            original_filename="Naukri_jyotiSaxena9y_1m.pdf"
        )
        
        print("\n" + "="*60)
        print(" ✅ EXTRACTION SUCCESSFUL!")
        print("="*60 + "\n")
        
        print(f"Anonymized ID: {intelligence['anonymized_id']}")
        print(f"Verdict: {intelligence['verdict']}")
        print(f"Confidence: {intelligence['confidence_score']}%")
        print(f"\nYears Experience: {intelligence.get('years_of_experience', 'N/A')}")
        print(f"Career Level: {intelligence.get('career_level', 'N/A')}")
        
        print(f"\nTop Skills: {', '.join(intelligence.get('key_skills', [])[:5])}")
        
        print(f"\nVerdict Reason:")
        print(f"  {intelligence.get('evidence_based_reasoning', 'N/A')[:200]}...")
        
        # Store in database
        print("\n" + "-"*60)
        print("💾 Storing in Supabase database...\n")
        
        storage = SupabaseStorage()
        storage.store_intelligence(intelligence)
        print("✓ Stored successfully!")
        
        # Check database stats
        stats = storage.get_statistics()
        print(f"\n📊 Database Statistics:")
        print(f"  Total candidates: {stats['total_candidates']}")
        print(f"  Shortlisted: {stats['shortlisted']}")
        print(f"  Backup: {stats['backup']}")
        print(f"  Review needed: {stats['review_needed']}")
        
        print("\n" + "="*60)
        print(" 🎉 TEST COMPLETE - Everything Working!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_single_cv()
