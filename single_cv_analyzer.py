"""
Single CV Analyzer - Quick LLM analysis for individual CVs
"""

import sys
import json
from pathlib import Path
from llm_batch_processor import LLMBatchProcessor


def main():
    if len(sys.argv) < 2:
        print("Usage: python single_cv_analyzer.py <cv_file> [job_description_file] [--provider <openai|anthropic|gemini>]")
        print("\nExample:")
        print("  python single_cv_analyzer.py final_output/REDACTED_CV_Jonny_Kanwar.txt")
        print("  python single_cv_analyzer.py final_output/REDACTED_CV_Jonny_Kanwar.txt job.txt")
        print("  python single_cv_analyzer.py final_output/REDACTED_CV_Jonny_Kanwar.txt job.txt --provider gemini")
        return 1
    
    cv_file = Path(sys.argv[1])
    if not cv_file.exists():
        print(f"❌ CV file not found: {cv_file}")
        return 1
    
    # Parse provider argument
    provider = "gemini"  # Default to Gemini
    if "--provider" in sys.argv:
        provider_idx = sys.argv.index("--provider")
        if provider_idx + 1 < len(sys.argv):
            provider = sys.argv[provider_idx + 1]
    
    # Read CV
    with open(cv_file, 'r', encoding='utf-8') as f:
        cv_text = f.read()
    
    # Read JD if provided
    job_description = None
    if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
        jd_file = Path(sys.argv[2])
        if jd_file.exists():
            with open(jd_file, 'r', encoding='utf-8') as f:
                job_description = f.read()
            print(f"📋 Using job description: {jd_file.name}")
        else:
            print(f"⚠️  JD file not found: {jd_file}")
    
    # Initialize processor
    print(f"\n🔍 Analyzing: {cv_file.name}")
    print(f"🤖 Provider: {provider.upper()}")
    processor = LLMBatchProcessor(api_provider=provider)
    
    # Process CV
    result = processor.process_single_cv(cv_text, cv_file.name, job_description)
    
    # Display results
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80)
    
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        if "error_message" in result:
            print(f"   {result['error_message']}")
        return 1
    
    # Metadata
    meta = result.get("metadata", {})
    print(f"\n📊 CANDIDATE PROFILE")
    print(f"   Experience: {meta.get('total_years_experience', 'N/A')} years total, {meta.get('relevant_years_experience', 'N/A')} years relevant")
    print(f"   Seniority: {meta.get('seniority_level', 'N/A')}")
    print(f"   Team Leadership: {'Yes' if meta.get('has_team_leadership') else 'No'}")
    print(f"   Industries: {', '.join(meta.get('industries', []))}")
    
    # Skills
    print(f"\n💡 TECHNICAL SKILLS")
    core_skills = meta.get('core_technical_skills', [])
    if core_skills:
        print(f"   Core: {', '.join(core_skills[:8])}")
        if len(core_skills) > 8:
            print(f"         + {len(core_skills) - 8} more")
    
    tools = meta.get('tools_and_frameworks', [])
    if tools:
        print(f"   Tools: {', '.join(tools[:6])}")
        if len(tools) > 6:
            print(f"          + {len(tools) - 6} more")
    
    domains = meta.get('domain_expertise', [])
    if domains:
        print(f"   Domains: {', '.join(domains)}")
    
    # JD Fitment
    jd_fit = result.get("jd_fitment")
    if jd_fit:
        print(f"\n🎯 JD FITMENT")
        print(f"   Confidence Score: {jd_fit.get('confidence_score', 'N/A')}/100")
        
        met = jd_fit.get('mandatory_requirements_met', [])
        if met:
            print(f"   ✅ Requirements Met: {', '.join(met)}")
        
        missing = jd_fit.get('mandatory_requirements_missing', [])
        if missing:
            print(f"   ❌ Requirements Missing: {', '.join(missing)}")
        
        nice = jd_fit.get('nice_to_have_skills_present', [])
        if nice:
            print(f"   ⭐ Nice-to-Have: {', '.join(nice)}")
    
    # Verdict
    verdict = result.get("verdict", "N/A")
    verdict_colors = {
        "SHORTLIST": "🟢",
        "BACKUP": "🟡",
        "REJECT": "🔴",
        "PENDING JD": "⚪"
    }
    
    print(f"\n{'='*80}")
    print(f"{verdict_colors.get(verdict, '⚪')} VERDICT: {verdict}")
    print(f"{'='*80}")
    print(f"\n{result.get('reason', 'N/A')}")
    
    # Narrative
    print(f"\n📝 PROFESSIONAL NARRATIVE")
    print("─" * 80)
    narrative = result.get('cleaned_narrative', '')
    # Wrap text
    words = narrative.split()
    line = []
    for word in words:
        if len(' '.join(line + [word])) <= 78:
            line.append(word)
        else:
            print(' '.join(line))
            line = [word]
    if line:
        print(' '.join(line))
    
    # Save to file
    output_file = Path("llm_analysis") / f"single_analysis_{cv_file.stem}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full results saved to: {output_file}")
    print("")
    
    return 0


if __name__ == "__main__":
    exit(main())
