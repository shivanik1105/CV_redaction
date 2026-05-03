# Quick Deployment Script for Render
# This script helps you prepare your code for Render deployment

param(
    [switch]$Init,
    [switch]$Push
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CV INTELLIGENCE SYSTEM - RENDER DEPLOYMENT" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if Git is installed
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitInstalled) {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

if ($Init) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    
    # Initialize Git if not already done
    if (-not (Test-Path ".git")) {
        git init
        Write-Host "✓ Git repository initialized" -ForegroundColor Green
    } else {
        Write-Host "✓ Git repository already exists" -ForegroundColor Green
    }
    
    # Create .gitignore if not exists
    if (-not (Test-Path ".gitignore")) {
        Write-Host "Creating .gitignore..." -ForegroundColor Yellow
        @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Environment variables
.env
.env.local

# User data
users.json
uploads/
redacted_output/
llm_analysis/
intelligence_output/
test_results/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.egg-info/

# Logs
*.log
"@ | Out-File -FilePath .gitignore -Encoding utf8
        Write-Host "✓ .gitignore created" -ForegroundColor Green
    }
    
    # Add all files
    Write-Host "Adding files to Git..." -ForegroundColor Yellow
    git add .
    
    # Commit
    Write-Host "Creating initial commit..." -ForegroundColor Yellow
    git commit -m "Initial commit - CV Intelligence System with authentication"
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host "INITIALIZATION COMPLETE!" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Create a GitHub repository" -ForegroundColor White
    Write-Host "2. Run: git remote add origin https://github.com/YOUR_USERNAME/cv-intelligence-system.git" -ForegroundColor White
    Write-Host "3. Run: .\deploy_to_render.ps1 -Push" -ForegroundColor White
    Write-Host ""
}

if ($Push) {
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    
    # Check if remote exists
    $remote = git remote -v 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $remote) {
        Write-Host "ERROR: No Git remote configured!" -ForegroundColor Red
        Write-Host "Please add a remote first:" -ForegroundColor Yellow
        Write-Host "  git remote add origin https://github.com/YOUR_USERNAME/cv-intelligence-system.git" -ForegroundColor White
        exit 1
    }
    
    # Push to main branch
    Write-Host "Pushing to main branch..." -ForegroundColor Yellow
    git branch -M main
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host "PUSH SUCCESSFUL!" -ForegroundColor Green
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Go to https://render.com" -ForegroundColor White
        Write-Host "2. Click 'New +' → 'Web Service'" -ForegroundColor White
        Write-Host "3. Connect your GitHub repository" -ForegroundColor White
        Write-Host "4. Follow the guide in RENDER_DEPLOYMENT_GUIDE.md" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "ERROR: Push failed!" -ForegroundColor Red
        Write-Host "Please check your Git configuration and try again." -ForegroundColor Yellow
    }
}

if (-not $Init -and -not $Push) {
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\deploy_to_render.ps1 -Init    # Initialize Git repository" -ForegroundColor White
    Write-Host "  .\deploy_to_render.ps1 -Push    # Push to GitHub" -ForegroundColor White
    Write-Host ""
    Write-Host "Full deployment guide: RENDER_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
    Write-Host ""
}
