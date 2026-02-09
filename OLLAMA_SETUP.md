# 🆓 Ollama Setup - FREE Local LLM (No API Key Needed!)

## What is Ollama?
**Ollama** lets you run powerful AI models **locally on your computer** - completely free, private, and unlimited!

**Benefits:**
- ✅ **100% FREE** - No API keys, no credit card
- ✅ **No rate limits** - Process unlimited CVs
- ✅ **Private** - Data never leaves your computer
- ✅ **Fast** - No network latency
- ✅ **Works offline** - No internet needed

---

## Quick Setup (5 minutes)

### Step 1: Download Ollama
```powershell
# Open PowerShell and run:
winget install Ollama.Ollama

# OR download manually from:
# https://ollama.com/download/windows
```

### Step 2: Install a Model
```powershell
# Install recommended model (7B - good balance of speed & quality)
ollama pull qwen2.5:7b

# OR use smaller/faster model (3B - faster but slightly lower quality)
ollama pull qwen2.5:3b

# OR use larger model (14B - higher quality but slower)
ollama pull qwen2.5:14b
```

### Step 3: Test It!
```powershell
# Analyze single CV
python single_cv_analyzer.py "final_output/REDACTED_CV Jonny Kanwar.txt" example_job_description.txt

# Batch process (default provider is now Ollama!)
python llm_batch_processor.py --limit 3

# Or explicitly specify Ollama
python llm_batch_processor.py --provider ollama --limit 5
```

---

## One-Click Setup Script

Run this in PowerShell:

```powershell
# Complete Ollama setup and first run
function Setup-Ollama {
    Write-Host "`n=== Ollama Setup (FREE Local LLM) ===" -ForegroundColor Cyan
    
    # Check if Ollama is installed
    $ollamaInstalled = Get-Command ollama -ErrorAction SilentlyContinue
    
    if (-not $ollamaInstalled) {
        Write-Host "`n[1/3] Installing Ollama..." -ForegroundColor Yellow
        winget install Ollama.Ollama
        
        # Wait for installation
        Start-Sleep -Seconds 5
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "`n✅ Ollama already installed!" -ForegroundColor Green
    }
    
    # Pull model
    Write-Host "`n[2/3] Downloading AI model (qwen2.5:7b - 4.7GB)..." -ForegroundColor Yellow
    Write-Host "This may take 5-10 minutes on first run..." -ForegroundColor Gray
    ollama pull qwen2.5:7b
    
    # Test
    Write-Host "`n[3/3] Testing with single CV..." -ForegroundColor Yellow
    python single_cv_analyzer.py "final_output\REDACTED_CV Jonny Kanwar.txt" example_job_description.txt
    
    Write-Host "`n✅ Setup complete! Ollama is ready to use!" -ForegroundColor Green
    Write-Host "`nProcess all CVs: python llm_batch_processor.py" -ForegroundColor Cyan
}

# Run setup
Setup-Ollama
```

---

## Available Models

### Recommended: Qwen 2.5 (Best for JSON/Structured Output)
```powershell
ollama pull qwen2.5:3b   # 2GB - Fast, good for testing
ollama pull qwen2.5:7b   # 4.7GB - RECOMMENDED (best balance)
ollama pull qwen2.5:14b  # 9GB - Highest quality
```

### Alternative: Llama 3.2
```powershell
ollama pull llama3.2:3b  # 2GB - Fast
ollama pull llama3.2:8b  # 5GB - Good quality
```

### Alternative: Mistral
```powershell
ollama pull mistral:7b   # 4.1GB - Good general purpose
```

**How to use different models:**
```powershell
python llm_batch_processor.py --provider ollama --model qwen2.5:3b
```

---

## Usage Examples

### Basic Usage (Uses Ollama by default now!)
```powershell
# Process all CVs
python llm_batch_processor.py

# With job description
python llm_batch_processor.py --jd job_description.txt

# Limit to 10 CVs
python llm_batch_processor.py --limit 10
```

### Specify Model
```powershell
# Use faster 3B model
python llm_batch_processor.py --model qwen2.5:3b --limit 5

# Use higher quality 14B model
python llm_batch_processor.py --model qwen2.5:14b --limit 5
```

### Single CV Analysis
```powershell
python single_cv_analyzer.py "final_output/REDACTED_CV Jonny Kanwar.txt" example_job_description.txt
```

### Complete Pipeline
```powershell
# Redact + Analyze with Ollama
.\analyze_resumes.ps1 -JobDescription example_job_description.txt
```

---

## Performance Comparison

| Model | Speed (per CV) | Quality | RAM Needed | Disk Space |
|-------|---------------|---------|------------|------------|
| qwen2.5:3b | ~5-8s | Good | 4GB | 2GB |
| qwen2.5:7b ⭐ | ~10-15s | Excellent | 8GB | 4.7GB |
| qwen2.5:14b | ~20-30s | Best | 16GB | 9GB |
| llama3.2:3b | ~6-10s | Good | 4GB | 2GB |

**Recommended:** qwen2.5:7b - Best balance of speed, quality, and resource usage

---

## Troubleshooting

### Ollama not found after install
```powershell
# Close and reopen PowerShell, then:
ollama --version

# If still not found, restart computer
```

### Model download stuck
```powershell
# Press Ctrl+C and retry
ollama pull qwen2.5:7b
```

### "Connection refused" error
```powershell
# Ollama should start automatically. If not:
ollama serve

# In new terminal:
python llm_batch_processor.py
```

### Out of memory
```powershell
# Use smaller model
ollama pull qwen2.5:3b
python llm_batch_processor.py --model qwen2.5:3b
```

### Slow performance
- Use qwen2.5:3b instead of 7b
- Close other applications
- Ensure enough RAM (8GB+ recommended)

---

## FAQ

**Q: Is Ollama really free?**  
A: Yes! 100% free, no hidden costs, no subscriptions.

**Q: Do I need GPU?**  
A: No! Works on CPU (faster with GPU but not required).

**Q: Can I use it offline?**  
A: Yes! Once model is downloaded, works completely offline.

**Q: How much disk space needed?**  
A: ~5GB for qwen2.5:7b model + Ollama (~500MB)

**Q: Is it as good as GPT-4?**  
A: For structured CV analysis, qwen2.5:7b is excellent! Slightly lower quality than GPT-4 but 100% free.

**Q: Can I use other models?**  
A: Yes! See all models at https://ollama.com/library

---

## Comparison with Cloud APIs

| Feature | Ollama (qwen2.5:7b) | OpenAI GPT-4o | Gemini | Anthropic |
|---------|---------------------|---------------|--------|-----------|
| **Cost** | **FREE** ⭐ | $2.50/50 CVs | $1/50 CVs | $4/50 CVs |
| **Rate Limits** | **None** ⭐ | 500/day | 60/min | 50/min |
| **Privacy** | **Local** ⭐ | Cloud | Cloud | Cloud |
| **Speed** | 10-15s/CV | 2-3s/CV | 1-2s/CV | 2-3s/CV |
| **Quality** | Excellent | Best | Excellent | Excellent |
| **Setup** | 5 min | 1 min | 1 min | 1 min |

**Winner for CV Analysis:** Ollama! Free, unlimited, private, and excellent quality.

---

## Next Steps

1. ✅ Run the one-click setup script above
2. ✅ Test with 3 CVs: `python llm_batch_processor.py --limit 3`
3. ✅ Process all CVs: `python llm_batch_processor.py --jd job.txt`
4. ✅ Enjoy unlimited free CV analysis! 🎉

**Need help?** Check troubleshooting section above or open an issue.
