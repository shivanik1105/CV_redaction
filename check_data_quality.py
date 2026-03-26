"""
Check data quality issues in CV intelligence data
Identifies all types of inconsistencies and data quality problems
"""
import json
from pathlib import Path

def check_all_data_quality_issues():
    """Comprehensive data quality check"""
    intelligence_dir = Path('llm_analysis')
    issues = []
    stats = {
        'total_files': 0,
        'valid_files': 0,
        'error_files': 0
    }
    
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        stats['total_files'] += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'error' in data and not data.get('verdict'):
                stats['error_files'] += 1
                continue
            
            stats['valid_files'] += 1
            anon_id = data.get('anonymized_id', 'UNKNOWN')
            years = data.get('years_experience', 0)
            seniority = data.get('seniority_level', 'N/A')
            verdict = data.get('verdict', 'N/A')
            confidence = data.get('confidence_score', 0)
            match_score = data.get('match_score', 0)
            
            # Issue 1: Zero years but senior level
            if years == 0 and seniority in ['MID', 'SENIOR', 'LEAD', 'EXECUTIVE']:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'zero_years_senior',
                    'issue': f'0 years but {seniority} level',
                    'severity': 'high',
                    'years_experience': years,
                    'seniority_level': seniority
                })
            
            # Issue 2: Negative years
            if years < 0:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'negative_years',
                    'issue': f'Negative years: {years}',
                    'severity': 'critical',
                    'years_experience': years
                })
            
            # Issue 3: Unrealistic years (>50)
            if years > 50:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'unrealistic_years',
                    'issue': f'Unrealistic years: {years}',
                    'severity': 'high',
                    'years_experience': years
                })
            
            # Issue 4: Entry level with many years
            if seniority == 'ENTRY' and years > 3:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'entry_many_years',
                    'issue': f'ENTRY level but {years} years',
                    'severity': 'medium',
                    'years_experience': years,
                    'seniority_level': seniority
                })
            
            # Issue 5: Executive with few years
            if seniority == 'EXECUTIVE' and 0 < years < 10:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'executive_few_years',
                    'issue': f'EXECUTIVE but only {years} years',
                    'severity': 'medium',
                    'years_experience': years,
                    'seniority_level': seniority
                })
            
            # Issue 6: Missing core technical skills
            if not data.get('core_technical_skills'):
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'missing_skills',
                    'issue': 'No core technical skills',
                    'severity': 'high'
                })
            
            # Issue 7: Missing primary domain
            if not data.get('primary_domain'):
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'missing_domain',
                    'issue': 'No primary domain',
                    'severity': 'medium'
                })
            
            # Issue 8: Invalid verdict
            if verdict not in ['SHORTLIST', 'BACKUP', 'REVIEW', 'REJECT']:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'invalid_verdict',
                    'issue': f'Invalid verdict: {verdict}',
                    'severity': 'high',
                    'verdict': verdict
                })
            
            # Issue 9: Low confidence with SHORTLIST
            if verdict == 'SHORTLIST' and confidence < 60:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'shortlist_low_confidence',
                    'issue': f'SHORTLIST but only {confidence}% confidence',
                    'severity': 'medium',
                    'confidence_score': confidence
                })
            
            # Issue 10: High confidence with REJECT
            if verdict == 'REJECT' and confidence > 80:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'reject_high_confidence',
                    'issue': f'REJECT but {confidence}% confidence',
                    'severity': 'low',
                    'confidence_score': confidence
                })
            
            # Issue 11: Match score and confidence mismatch
            if abs(match_score - confidence) > 30:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'score_mismatch',
                    'issue': f'Match {match_score}% vs Confidence {confidence}%',
                    'severity': 'low',
                    'match_score': match_score,
                    'confidence_score': confidence
                })
            
            # Issue 12: Missing verdict reason
            if not data.get('verdict_reason'):
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'missing_reason',
                    'issue': 'No verdict reason',
                    'severity': 'low'
                })
            
            # Issue 13: Empty or very short narrative
            narrative = data.get('cleaned_narrative', '')
            if len(narrative) < 50:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'short_narrative',
                    'issue': f'Narrative too short ({len(narrative)} chars)',
                    'severity': 'medium'
                })
            
            # Issue 14: Invalid seniority level
            valid_seniority = ['ENTRY', 'MID', 'SENIOR', 'LEAD', 'EXECUTIVE', 'N/A']
            if seniority not in valid_seniority:
                issues.append({
                    'file': json_file.name,
                    'anonymized_id': anon_id,
                    'issue_type': 'invalid_seniority',
                    'issue': f'Invalid seniority: {seniority}',
                    'severity': 'high',
                    'seniority_level': seniority
                })
        
        except Exception as e:
            stats['error_files'] += 1
            issues.append({
                'file': json_file.name,
                'anonymized_id': 'UNKNOWN',
                'issue_type': 'file_error',
                'issue': f'Error reading file: {str(e)}',
                'severity': 'critical'
            })
    
    return issues, stats

if __name__ == '__main__':
    print("🔍 Running comprehensive data quality check...\n")
    
    issues, stats = check_all_data_quality_issues()
    
    print(f"📊 File Statistics:")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Valid files: {stats['valid_files']}")
    print(f"  Error files: {stats['error_files']}")
    print()
    
    if not issues:
        print("✅ No data quality issues found!")
    else:
        print(f"⚠️ Found {len(issues)} data quality issues:\n")
        
        # Group by issue type and severity
        by_type = {}
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        
        for issue in issues:
            issue_type = issue['issue_type']
            severity = issue['severity']
            
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
            by_severity[severity].append(issue)
        
        # Show by severity
        print("=" * 70)
        print("ISSUES BY SEVERITY")
        print("=" * 70)
        
        for severity in ['critical', 'high', 'medium', 'low']:
            items = by_severity[severity]
            if items:
                print(f"\n🔴 {severity.upper()}: {len(items)} issues")
                print("-" * 70)
                
                # Group by type within severity
                types_in_severity = {}
                for item in items:
                    t = item['issue_type']
                    if t not in types_in_severity:
                        types_in_severity[t] = []
                    types_in_severity[t].append(item)
                
                for issue_type, type_items in types_in_severity.items():
                    print(f"  {issue_type}: {len(type_items)} cases")
                    for item in type_items[:3]:  # Show first 3
                        print(f"    - {item['anonymized_id']}: {item['issue']}")
                    if len(type_items) > 3:
                        print(f"    ... and {len(type_items) - 3} more")
        
        print("\n" + "=" * 70)
        print(f"TOTAL ISSUES: {len(issues)}")
        print("=" * 70)
        
        print("\n📋 Recommendations:")
        print("1. CRITICAL issues need immediate attention")
        print("2. HIGH issues affect data accuracy - consider re-processing")
        print("3. MEDIUM issues are minor inconsistencies")
        print("4. LOW issues are cosmetic/optional")
        print("\n✅ Frontend has been updated to handle these gracefully")

