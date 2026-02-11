# Quick Setup Script for CV Intelligence System
# Run this after setting your API keys

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CV Intelligence System - Quick Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found`n" -ForegroundColor Green

# Check API Keys
Write-Host "Checking API Keys..." -ForegroundColor Yellow
$llmConfigured = $false

if ($env:GOOGLE_API_KEY) {
    Write-Host "✓ Google Gemini API key found" -ForegroundColor Green
    $llmConfigured = $true
} elseif ($env:OPENAI_API_KEY) {
    Write-Host "✓ OpenAI API key found" -ForegroundColor Green
    $llmConfigured = $true
} elseif ($env:ANTHROPIC_API_KEY) {
    Write-Host "✓ Anthropic API key found" -ForegroundColor Green
    $llmConfigured = $true
} else {
    Write-Host "⚠️  No LLM API key found. You can use Ollama (free, local) or set:" -ForegroundColor Yellow
    Write-Host "  `$env:GOOGLE_API_KEY='your-key'" -ForegroundColor Gray
    Write-Host "  Will use Ollama if available`n" -ForegroundColor Gray
}

# Check Supabase
Write-Host "Checking Supabase configuration..." -ForegroundColor Yellow
if ($env:SUPABASE_URL -and $env:SUPABASE_KEY) {
    Write-Host "✓ Supabase configured`n" -ForegroundColor Green
} else {
    Write-Host "⚠️  Supabase not configured. Set these for database features:" -ForegroundColor Yellow
    Write-Host "  `$env:SUPABASE_URL='https://your-project.supabase.co'" -ForegroundColor Gray
    Write-Host "  `$env:SUPABASE_KEY='your-anon-key'`n" -ForegroundColor Gray
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed`n" -ForegroundColor Green

# Download spaCy model
Write-Host "Downloading spaCy language model..." -ForegroundColor Yellow
python -m spacy download en_core_web_sm --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Failed to download spaCy model (may already exist)" -ForegroundColor Yellow
} else {
    Write-Host "✓ spaCy model ready`n" -ForegroundColor Green
}

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
$dirs = @("uploads", "redacted_output", "llm_analysis", "templates", "static")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created $dir/" -ForegroundColor Gray
    }
}
Write-Host "✓ Directories ready`n" -ForegroundColor Green

# Supabase setup instructions
if ($env:SUPABASE_URL -and $env:SUPABASE_KEY) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Supabase Database Setup Required" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "Run this command to get the SQL setup script:" -ForegroundColor Yellow
    Write-Host "  python supabase_storage.py --action setup`n" -ForegroundColor White
    
    Write-Host "Then:" -ForegroundColor Yellow
    Write-Host "  1. Copy the SQL output" -ForegroundColor Gray
    Write-Host "  2. Go to your Supabase dashboard" -ForegroundColor Gray
    Write-Host "  3. Open SQL Editor" -ForegroundColor Gray
    Write-Host "  4. Paste and execute the SQL`n" -ForegroundColor Gray
}

# Setup complete
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. If using Supabase, run the database setup (see above)" -ForegroundColor White
Write-Host "  2. Start the web app:" -ForegroundColor White
Write-Host "     python app.py`n" -ForegroundColor Cyan
Write-Host "  3. Open http://localhost:5000 in your browser`n" -ForegroundColor White

Write-Host "Quick Commands:" -ForegroundColor Yellow
Write-Host "  Upload CVs:     http://localhost:5000" -ForegroundColor Gray
Write-Host "  Dashboard:      http://localhost:5000/dashboard" -ForegroundColor Gray
Write-Host "  Health Check:   http://localhost:5000/health`n" -ForegroundColor Gray

Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  Complete Guide: INTELLIGENCE_SYSTEM_GUIDE.md" -ForegroundColor Gray
Write-Host "  Quick Start:    QUICKSTART.md" -ForegroundColor Gray
Write-Host "  LLM Setup:      LLM_QUICKSTART.md`n" -ForegroundColor Gray

Write-Host "========================================`n" -ForegroundColor Cyan
