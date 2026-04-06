#!/usr/bin/env python3
"""
Script to update frontend templates by removing verdict-related code
"""
import re
from pathlib import Path

def update_index_new():
    """Update index_new.html to remove verdict references"""
    file_path = Path('templates/index_new.html')
    
    if not file_path.exists():
        print(f"❌ {file_path} not found")
        return
    
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Remove shortlisted stat card
    content = re.sub(
        r'<div class="stat-card">.*?<div class="stat-number" id="shortlistCVs">.*?</div>.*?<div class="stat-label">Shortlisted</div>.*?</div>',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Remove verdict filter
    content = re.sub(
        r'<div class="form-group">.*?<label>Verdict</label>.*?<select id="filterVerdict">.*?</select>.*?</div>',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Update JavaScript - remove verdict from filters
    content = content.replace(
        "verdict: document.getElementById('filterVerdict').value,",
        "// verdict filter removed"
    )
    
    # Update JavaScript - remove verdict filtering
    content = re.sub(
        r"if \(filters\.verdict\) \{.*?matches = matches\.filter\(m => m\.verdict === filters\.verdict\);.*?\}",
        "// verdict filtering removed",
        content,
        flags=re.DOTALL
    )
    
    # Update clear filters
    content = content.replace(
        "document.getElementById('filterVerdict').value = '';",
        "// verdict filter removed"
    )
    
    # Replace verdict_reason with assessment_reason
    content = content.replace('verdict_reason', 'assessment_reason')
    
    # Replace verdict display with confidence
    content = re.sub(
        r'<strong>Verdict:</strong> \$\{.*?verdictLabel.*?\}',
        '<strong>Confidence:</strong> ${candidate.confidence_score}%',
        content
    )
    
    # Update recruiter decision buttons
    content = re.sub(
        r"onclick=\"submitRecruiterDecision\('.*?', 'SHORTLIST'\)\">Shortlist</button>",
        "onclick=\"submitRecruiterDecision('${candidate.anonymized_id}', 'HIRED')\">Hire</button>",
        content
    )
    
    content = re.sub(
        r"onclick=\"submitRecruiterDecision\('.*?', 'REJECT'\)\">Reject</button>",
        "// Reject button removed",
        content
    )
    
    if content != original_content:
        # Backup original
        backup_path = file_path.with_suffix('.html.backup')
        backup_path.write_text(original_content, encoding='utf-8')
        print(f"✅ Backed up original to {backup_path}")
        
        # Write updated content
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ Updated {file_path}")
        print(f"   - Removed verdict filter")
        print(f"   - Removed shortlisted stat")
        print(f"   - Updated JavaScript")
        print(f"   - Replaced verdict_reason with assessment_reason")
    else:
        print(f"ℹ️  No changes needed for {file_path}")


def swap_dashboard():
    """Swap dashboard.html with dashboard_new.html"""
    old_dashboard = Path('templates/dashboard.html')
    new_dashboard = Path('templates/dashboard_new.html')
    backup_dashboard = Path('templates/dashboard_old.html')
    
    if not new_dashboard.exists():
        print(f"❌ {new_dashboard} not found")
        return
    
    if old_dashboard.exists():
        # Backup old dashboard
        old_dashboard.rename(backup_dashboard)
        print(f"✅ Backed up old dashboard to {backup_dashboard}")
    
    # Rename new dashboard to main
    new_dashboard.rename(old_dashboard)
    print(f"✅ Activated new dashboard (verdict-free)")


def main():
    print("=" * 60)
    print("Frontend Verdict Removal Script")
    print("=" * 60)
    print()
    
    print("Step 1: Updating index_new.html...")
    update_index_new()
    print()
    
    print("Step 2: Swapping dashboard...")
    swap_dashboard()
    print()
    
    print("=" * 60)
    print("✅ Frontend updates complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test the application: python app.py")
    print("2. Check for any JavaScript errors in browser console")
    print("3. Verify all pages load correctly")
    print("4. Review FRONTEND_VERDICT_REMOVAL_GUIDE.md for details")


if __name__ == '__main__':
    main()
