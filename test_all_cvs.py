"""
Test all CVs in the samples folder and generate a report
"""
import os
from pathlib import Path
from universal_pipeline_engine import PipelineOrchestrator
import time

def check_quality(text, filename):
    """Check the quality of the extracted text"""
    issues = []
    warnings = []
    
    # Check for empty sections
    if 'SUMMARY\n\n\n\nSKILLS' in text or 'SUMMARY\n\n\nSKILLS' in text:
        issues.append("Empty SUMMARY or SKILLS sections detected")
    
    # Check for minimum content
    if len(text.strip()) < 200:
        issues.append(f"Text too short ({len(text)} chars)")
    
    # Check for proper structure
    lines = text.split('\n')
    non_empty_lines = [l for l in lines if l.strip()]
    
    if len(non_empty_lines) < 10:
        issues.append(f"Too few content lines ({len(non_empty_lines)})")
    
    # Check for common section headers
    text_upper = text.upper()
    has_experience = any(kw in text_upper for kw in ['EXPERIENCE', 'WORK HISTORY', 'EMPLOYMENT'])
    has_education = 'EDUCATION' in text_upper
    has_skills = 'SKILL' in text_upper
    
    if not has_experience:
        warnings.append("No EXPERIENCE section found")
    if not has_education:
        warnings.append("No EDUCATION section found")
    if not has_skills:
        warnings.append("No SKILLS section found")
    
    # Check for redaction
    has_redactions = any(tag in text for tag in ['[REDACTED_NAME]', '[REDACTED_EMAIL]', '[REDACTED_PHONE]'])
    if not has_redactions:
        warnings.append("No PII redactions found (might be okay)")
    
    return issues, warnings

def test_cv(pdf_path, orchestrator):
    """Test a single CV"""
    filename = Path(pdf_path).name
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print(f"{'='*80}")
    
    try:
        start_time = time.time()
        redacted_text, profile = orchestrator.process_cv(str(pdf_path))
        elapsed = time.time() - start_time
        
        # Save output
        output_dir = Path("test_results")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{Path(filename).stem}_output.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
        
        # Check quality
        issues, warnings = check_quality(redacted_text, filename)
        
        # Print results
        print(f"CV Type: {profile.cv_type}")
        print(f"Confidence: {profile.confidence:.1%}")
        print(f"Processing Time: {elapsed:.1f}s")
        print(f"Text Length: {len(redacted_text)} chars")
        print(f"Lines: {len(redacted_text.split(chr(10)))}")
        print(f"Output: {output_file}")
        
        if issues:
            print(f"\n[!] ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        
        if warnings:
            print(f"\n[!] WARNINGS:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if not issues and not warnings:
            print(f"\n[OK] PASSED - No issues detected")
        elif not issues:
            print(f"\n[OK] PASSED - Minor warnings only")
        else:
            print(f"\n[FAIL] FAILED - Issues need attention")
        
        # Show preview
        print(f"\nPreview (first 500 chars):")
        print("-" * 80)
        print(redacted_text[:500])
        print("-" * 80)
        
        return {
            'filename': filename,
            'success': True,
            'cv_type': str(profile.cv_type),
            'confidence': profile.confidence,
            'elapsed': elapsed,
            'length': len(redacted_text),
            'lines': len(redacted_text.split('\n')),
            'issues': issues,
            'warnings': warnings,
            'output_file': str(output_file)
        }
        
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'filename': filename,
            'success': False,
            'error': str(e)
        }

def main():
    # Check multiple folders
    test_folders = []
    
    samples_dir = Path("samples")
    if samples_dir.exists():
        test_folders.append(samples_dir)
    
    samples_more_dir = Path("samples/more")
    if samples_more_dir.exists():
        test_folders.append(samples_more_dir)
    
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        test_folders.append(uploads_dir)
    
    if not test_folders:
        print("Error: No test folders found")
        return
    
    # Find all PDF files in all folders
    pdf_files = []
    for folder in test_folders:
        pdfs = list(folder.glob("*.pdf"))
        print(f"Found {len(pdfs)} PDFs in {folder}/")
        pdf_files.extend(pdfs)
    
    if not pdf_files:
        print(f"No PDF files found in test folders")
        return
    
    print("\n" + "=" * 80)
    print("CV EXTRACTION TEST - ALL SAMPLES")
    print("=" * 80)
    print(f"Test folders: {', '.join([str(f) for f in test_folders])}")
    print(f"Total PDF files: {len(pdf_files)}")
    print(f"Output directory: test_results/")
    print("=" * 80)
    
    # Initialize orchestrator once
    print("\nInitializing pipeline...")
    orchestrator = PipelineOrchestrator(debug=False, config_dir='config')
    print("Pipeline ready!\n")
    
    # Test all CVs
    results = []
    for pdf_file in sorted(pdf_files):
        result = test_cv(pdf_file, orchestrator)
        results.append(result)
        time.sleep(0.5)  # Small delay between tests
    
    # Generate summary report
    print("\n\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    passed = [r for r in successful if not r.get('issues')]
    passed_with_warnings = [r for r in successful if not r.get('issues') and r.get('warnings')]
    failed_quality = [r for r in successful if r.get('issues')]
    
    print(f"\nTotal CVs tested: {len(results)}")
    print(f"[OK] Passed: {len(passed)} ({len(passed)/len(results)*100:.1f}%)")
    print(f"[!] Passed with warnings: {len(passed_with_warnings)} ({len(passed_with_warnings)/len(results)*100:.1f}%)")
    print(f"[FAIL] Failed (quality issues): {len(failed_quality)} ({len(failed_quality)/len(results)*100:.1f}%)")
    print(f"[ERROR] Failed (errors): {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    
    if failed:
        print(f"\n[ERROR] FAILED (Errors):")
        for r in failed:
            print(f"  - {r['filename']}: {r.get('error', 'Unknown error')}")
    
    if failed_quality:
        print(f"\n[FAIL] FAILED (Quality Issues):")
        for r in failed_quality:
            print(f"  - {r['filename']}:")
            for issue in r['issues']:
                print(f"      * {issue}")
    
    if passed_with_warnings:
        print(f"\n[!] PASSED WITH WARNINGS:")
        for r in passed_with_warnings:
            print(f"  - {r['filename']}:")
            for warning in r['warnings']:
                print(f"      * {warning}")
    
    # Save detailed report
    report_file = Path("test_results/SUMMARY_REPORT.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CV EXTRACTION TEST - DETAILED REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        for r in results:
            f.write(f"\n{'='*80}\n")
            f.write(f"File: {r['filename']}\n")
            f.write(f"{'='*80}\n")
            
            if r['success']:
                f.write(f"Status: {'[OK] PASSED' if not r.get('issues') else '[FAIL] FAILED'}\n")
                f.write(f"CV Type: {r['cv_type']}\n")
                f.write(f"Confidence: {r['confidence']:.1%}\n")
                f.write(f"Processing Time: {r['elapsed']:.1f}s\n")
                f.write(f"Text Length: {r['length']} chars\n")
                f.write(f"Lines: {r['lines']}\n")
                f.write(f"Output: {r['output_file']}\n")
                
                if r.get('issues'):
                    f.write(f"\nIssues:\n")
                    for issue in r['issues']:
                        f.write(f"  - {issue}\n")
                
                if r.get('warnings'):
                    f.write(f"\nWarnings:\n")
                    for warning in r['warnings']:
                        f.write(f"  - {warning}\n")
            else:
                f.write(f"Status: [ERROR]\n")
                f.write(f"Error: {r.get('error', 'Unknown')}\n")
    
    print(f"\n\n[OK] Detailed report saved to: {report_file}")
    print(f"[OK] Individual outputs saved to: test_results/")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
