"""
Quick Search - Get Top 10 Matches for Job Description
NO LLM CALLS - Uses already-processed CVs in database
"""
import os
import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_triage import EnhancedTriageEngine


def quick_search(job_description: str, top_n: int = 10):
    """
    Search already-processed CVs and return top matches
    NO LLM CALLS - Pure keyword matching
    
    Args:
        job_description: Job description text
        top_n: Number of top matches to return
    
    Returns:
        List of top matching CVs with scores
    """
    print("=" * 70)
    print(f"Quick Search: Top {top_n} Matches")
    print("=" * 70)
    print(f"Job Description: {job_description[:100]}...")
    print()
    
    # Load already-processed CVs
    intelligence_dir = Path('llm_analysis')
    cvs = []
    
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Skip files with errors
            if 'error' in data and not data.get('verdict'):
                continue
            
            # Get CV text for matching
            cv_text = data.get('cleaned_narrative', '')
            if not cv_text:
                # Fallback to skills and domain
                skills = data.get('core_technical_skills', [])
                domain = data.get('primary_domain', '')
                cv_text = f"{domain} {' '.join(skills)}"
            
            cvs.append({
                'file': json_file.name,
                'data': data,
                'text': cv_text
            })
        except Exception as e:
            print(f"Warning: Error loading {json_file}: {e}")
    
    print(f"Found {len(cvs)} processed CVs in database")
    print()
    
    if not cvs:
        print("❌ No processed CVs found. Run 'Process All Sample CVs' first.")
        return []
    
    # Use enhanced triage for matching
    triage = EnhancedTriageEngine()
    matches = []
    
    for cv in cvs:
        should_process, reason, relevance_score = triage.should_process(cv['text'], job_description)
        match_percentage = relevance_score * 100
        
        # Extract matched keywords
        cv_keywords = triage.extract_keywords(cv['text'])
        jd_keywords = triage.extract_keywords(job_description)
        matched_keywords = list(cv_keywords.intersection(jd_keywords))
        
        matches.append({
            'anonymized_id': cv['data'].get('anonymized_id', 'UNKNOWN'),
            'file': cv['file'],
            'match_percentage': match_percentage,
            'matched_keywords': matched_keywords,
            'reason': reason,
            'verdict': cv['data'].get('verdict', 'UNKNOWN'),
            'confidence_score': cv['data'].get('confidence_score', 0),
            'years_experience': cv['data'].get('years_experience', 0),
            'seniority_level': cv['data'].get('seniority_level', 'UNKNOWN'),
            'core_skills': cv['data'].get('core_technical_skills', [])[:5],
            'primary_domain': cv['data'].get('primary_domain', 'Unknown'),
            'verdict_reason': cv['data'].get('verdict_reason', '')
        })
    
    # Sort by match percentage
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    
    # Get top N
    top_matches = matches[:top_n]
    
    # Display results
    print(f"Top {len(top_matches)} Matches:")
    print("=" * 70)
    
    for i, match in enumerate(top_matches, 1):
        print(f"\n{i}. {match['anonymized_id']} - Match: {match['match_percentage']:.1f}%")
        print(f"   File: {match['file']}")
        print(f"   Verdict: {match['verdict']} (Confidence: {match['confidence_score']}%)")
        print(f"   Experience: {match['years_experience']} years ({match['seniority_level']})")
        print(f"   Domain: {match['primary_domain']}")
        print(f"   Skills: {', '.join(match['core_skills'])}")
        print(f"   Matched Keywords: {', '.join(match['matched_keywords'][:10])}")
        if match['verdict_reason']:
            print(f"   Reason: {match['verdict_reason'][:150]}...")
    
    print("\n" + "=" * 70)
    print(f"✓ Search complete - {len(top_matches)} matches found")
    print("=" * 70)
    
    return top_matches


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick search for top CV matches')
    parser.add_argument(
        '--jd',
        type=str,
        help='Job description text'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Number of top matches to return (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Get job description
    if args.jd:
        job_description = args.jd
    else:
        print("Enter job description (press Ctrl+D or Ctrl+Z when done):")
        print()
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        job_description = '\n'.join(lines)
    
    if not job_description.strip():
        print("Error: Job description is required")
        sys.exit(1)
    
    # Search
    matches = quick_search(job_description, top_n=args.top)
    
    # Save results
    output_file = 'quick_search_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to {output_file}")
    
    sys.exit(0)


if __name__ == '__main__':
    main()
