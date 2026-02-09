# Ollama Setup Script - Installs and configures free local LLM
param(
    [string]$Model = "qwen2.5:7b"
)

Write-Host "`n========================================"
Write-Host "OLLAMA SETUP - FREE LOCAL LLM"
Write-Host "========================================`n"

# Check if Ollama is installed
Write-Host "[1/4] Checking Ollama installation..."
$ollamaExists = Get-Command ollama -ErrorAction SilentlyContinue

if (-not $ollamaExists) {
    Write-Host "Ollama not found. Attempting installation...`n"
    
    Write-Host "Please install Ollama manually:"
    Write-Host "1. Visit: https://ollama.com/download/windows"
    Write-Host "2. Download and run the Windows installer"
    Write-Host "3. After installation, run this script again`n"
    
    $open = Read-Host "Open download page in browser? (y/n)"
    if ($open -eq "y") {
        Start-Process "https://ollama.com/download/windows"
    }
    exit
}

Write-Host "[OK] Ollama is installed!`n"

# Pull model
Write-Host "[2/4] Checking model: $Model..."
$hasModel = ollama list | Select-String -Pattern $Model -Quiet

if (-not $hasModel) {
    Write-Host "Downloading model... (this may take 5-15 minutes)"
    Write-Host "Size: ~4.7GB for qwen2.5:7b`n"
    
    ollama pull $Model
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[ERROR] Model download failed."  
        Write-Host "Try smaller model: .\setup_ollama.ps1 -Model qwen2.5:3b"
        exit 1
    }
}

Write-Host "[OK] Model is ready!`n"

# Test service
Write-Host "[3/4] Testing Ollama service..."
try {
    ollama list | Out-Null
    Write-Host "[OK] Ollama service is running!`n"
} catch {
    Write-Host "Starting Ollama service..."
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# Test with CV
Write-Host "[4/4] Testing CV analysis..."
$cvFile = Get-ChildItem "final_output\REDACTED_*.txt" -ErrorAction SilentlyContinue | Select-Object -First 1

if ($cvFile) {
    Write-Host "Analyzing: $($cvFile.Name)"
    Write-Host "(First run may take 15-30 seconds)...`n"
    
    C:/Users/shiva/Downloads/samplecvs/resume/Scripts/python.exe single_cv_analyzer.py $cvFile.FullName example_job_description.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n========================================"
        Write-Host "SUCCESS! OLLAMA IS READY!"
        Write-Host "========================================`n"
        
        Write-Host "Process all CVs (free & unlimited!):"
        Write-Host "  python llm_batch_processor.py`n"
        
        Write-Host "With job description:"
        Write-Host "  python llm_batch_processor.py --jd job.txt`n"
        
        Write-Host "Process 10 CVs:"
        Write-Host "  python llm_batch_processor.py --limit 10`n"
    } else {
        Write-Host "`n[ERROR] Test failed. Check errors above."
    }
} else {
    Write-Host "[INFO] No CV files found.`n"
    Write-Host "First redact some CVs:"
    Write-Host "  python cv_redaction_pipeline.py resume/ final_output/`n"
    Write-Host "Then analyze:"
    Write-Host "  python llm_batch_processor.py"
}

Write-Host "`nDocumentation: OLLAMA_SETUP.md"
