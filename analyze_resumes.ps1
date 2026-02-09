# Complete CV Processing Pipeline
# Redacts CVs and analyzes them with LLM

param(
    [string]$InputDir = "resume",
    [string]$OutputDir = "final_output",
    [string]$JobDescription = "",
    [int]$Limit = 0
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CV PROCESSING PIPELINE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if API key is set
if (-not $env:OPENAI_API_KEY -and -not $env:ANTHROPIC_API_KEY -and -not $env:GOOGLE_API_KEY) {
    Write-Host "⚠️  WARNING: No API key found!" -ForegroundColor Yellow
    Write-Host "Please set one of the following environment variables:" -ForegroundColor Yellow
    Write-Host "  set OPENAI_API_KEY=your-key" -ForegroundColor Gray
    Write-Host "  set ANTHROPIC_API_KEY=your-key" -ForegroundColor Gray
    Write-Host "  set GOOGLE_API_KEY=your-key" -ForegroundColor Gray
    Write-Host ""
    $response = Read-Host "Do you want to continue anyway? (y/n)"
    if ($response -ne "y") {
        exit
    }
}

# Step 1: Redact CVs
Write-Host "📝 Step 1: Redacting CVs from $InputDir..." -ForegroundColor Cyan
python cv_redaction_pipeline.py $InputDir $OutputDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Redaction failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Redaction complete!`n" -ForegroundColor Green

# Count redacted files
$cvCount = (Get-ChildItem $OutputDir -Filter "REDACTED_*.txt").Count
Write-Host "📊 Found $cvCount redacted CVs`n" -ForegroundColor Cyan

# Step 2: Analyze with LLM
Write-Host "🤖 Step 2: Analyzing CVs with LLM..." -ForegroundColor Cyan

$llmArgs = @($OutputDir)

if ($JobDescription) {
    if (Test-Path $JobDescription) {
        $llmArgs += "--jd"
        $llmArgs += $JobDescription
        Write-Host "📋 Using job description: $JobDescription" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Job description file not found: $JobDescription" -ForegroundColor Yellow
    }
}

if ($Limit -gt 0) {
    $llmArgs += "--limit"
    $llmArgs += $Limit
    Write-Host "🔢 Processing limit: $Limit CVs" -ForegroundColor Gray
}

Write-Host ""
python llm_batch_processor.py @llmArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ LLM analysis failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ PIPELINE COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# Show results location
$latestResults = Get-ChildItem llm_analysis -Filter "batch_results_*.json" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1

if ($latestResults) {
    Write-Host "📊 Results saved to: $($latestResults.FullName)" -ForegroundColor Cyan
    
    # Quick summary
    $resultsContent = Get-Content $latestResults.FullName | ConvertFrom-Json
    $summary = $resultsContent.summary
    
    Write-Host "`nQUICK SUMMARY:" -ForegroundColor Yellow
    Write-Host "  Total CVs: $($summary.total)" -ForegroundColor White
    Write-Host "  Success: $($summary.success)" -ForegroundColor Green
    Write-Host "  Errors: $($summary.errors)" -ForegroundColor $(if ($summary.errors -gt 0) { "Red" } else { "Gray" })
    
    if ($summary.verdicts) {
        Write-Host "`n  VERDICTS:" -ForegroundColor Yellow
        if ($summary.verdicts.SHORTLIST) {
            Write-Host "    SHORTLIST: $($summary.verdicts.SHORTLIST)" -ForegroundColor Green
        }
        if ($summary.verdicts.BACKUP) {
            Write-Host "    BACKUP: $($summary.verdicts.BACKUP)" -ForegroundColor Cyan
        }
        if ($summary.verdicts.REJECT) {
            Write-Host "    REJECT: $($summary.verdicts.REJECT)" -ForegroundColor Gray
        }
        if ($summary.verdicts.'PENDING JD') {
            Write-Host "    PENDING JD: $($summary.verdicts.'PENDING JD')" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    $openFile = Read-Host "Open results file? (y/n)"
    if ($openFile -eq "y") {
        Invoke-Item $latestResults.FullName
    }
}
