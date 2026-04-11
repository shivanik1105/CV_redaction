# Push CV Intelligence System to GitHub
# Simple script to initialize Git and push to GitHub

param(
    [string]$RepoUrl = ""
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CV INTELLIGENCE SYSTEM - GITHUB PUSH" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if Git is installed
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitInstalled) {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Initialize Git if not already done
if (-not (Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✓ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✓ Git repository already exists" -ForegroundColor Green
}

# Check if .gitignore exists
if (-not (Test-Path ".gitignore")) {
    Write-Host "ERROR: .gitignore not found!" -ForegroundColor Red
    exit 1
}

# Add all files
Write-Host ""
Write-Host "Adding files to Git..." -ForegroundColor Yellow
git add .

# Show status
Write-Host ""
Write-Host "Files to be committed:" -ForegroundColor Yellow
git status --short

# Commit
Write-Host ""
Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "Initial commit - CV Intelligence System

Features:
- CV Redaction (PII removal)
- Intelligence Extraction (LLM)
- Job Description Matching
- Candidate Search & Ranking
- Supabase Integration
- Multi-column CV support
- Local JSON fallback

Ready for deployment to Render."

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Commit failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Commit created" -ForegroundColor Green

# Check if remote exists
$remote = git remote -v 2>&1
if ($LASTEXITCODE -ne 0 -or -not $remote) {
    if (-not $RepoUrl) {
        Write-Host ""
        Write-Host "=" * 80 -ForegroundColor Yellow
        Write-Host "NEXT STEPS:" -ForegroundColor Yellow
        Write-Host "=" * 80 -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Create a GitHub repository:" -ForegroundColor White
        Write-Host "   - Go to: https://github.com/new" -ForegroundColor Cyan
        Write-Host "   - Name: cv-intelligence-system" -ForegroundColor Cyan
        Write-Host "   - Public or Private (your choice)" -ForegroundColor Cyan
        Write-Host "   - Don't initialize with README" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "2. Add remote and push:" -ForegroundColor White
        Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/cv-intelligence-system.git" -ForegroundColor Cyan
        Write-Host "   git branch -M main" -ForegroundColor Cyan
        Write-Host "   git push -u origin main" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Or run this script with your repo URL:" -ForegroundColor White
        Write-Host "   .\push_to_github.ps1 -RepoUrl 'https://github.com/YOUR_USERNAME/cv-intelligence-system.git'" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "Adding remote repository..." -ForegroundColor Yellow
        git remote add origin $RepoUrl
        Write-Host "✓ Remote added" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
        git branch -M main
        git push -u origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "=" * 80 -ForegroundColor Green
            Write-Host "SUCCESS! CODE PUSHED TO GITHUB" -ForegroundColor Green
            Write-Host "=" * 80 -ForegroundColor Green
            Write-Host ""
            Write-Host "Repository: $RepoUrl" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Yellow
            Write-Host "1. Go to https://render.com" -ForegroundColor White
            Write-Host "2. Click 'New +' → 'Web Service'" -ForegroundColor White
            Write-Host "3. Connect your GitHub repository" -ForegroundColor White
            Write-Host "4. Configure environment variables:" -ForegroundColor White
            Write-Host "   - GROQ_API_KEY" -ForegroundColor Cyan
            Write-Host "   - SUPABASE_URL" -ForegroundColor Cyan
            Write-Host "   - SUPABASE_KEY" -ForegroundColor Cyan
            Write-Host "5. Deploy!" -ForegroundColor White
            Write-Host ""
            Write-Host "See RENDER_DEPLOYMENT_GUIDE.md for detailed instructions" -ForegroundColor Yellow
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "ERROR: Push failed!" -ForegroundColor Red
            Write-Host "Please check your GitHub credentials and repository URL" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host ""
    Write-Host "Remote repository already configured:" -ForegroundColor Yellow
    git remote -v
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git branch -M main
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host "SUCCESS! CODE PUSHED TO GITHUB" -ForegroundColor Green
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "ERROR: Push failed!" -ForegroundColor Red
        Write-Host "Please check your GitHub credentials" -ForegroundColor Yellow
    }
}
