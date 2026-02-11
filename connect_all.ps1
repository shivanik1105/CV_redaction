# Interactive Supabase Connection Setup
# This script helps you connect to Supabase step by step

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Connection Setup Wizard" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Check Google API Key
Write-Host "Step 1: Google Gemini API Key" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
if ($env:GOOGLE_API_KEY) {
    Write-Host "Google API Key is SET" -ForegroundColor Green
    $keyPreview = $env:GOOGLE_API_KEY.Substring(0, 20)
    Write-Host "  Key: $keyPreview..." -ForegroundColor Gray
} else {
    Write-Host "Google API Key NOT SET" -ForegroundColor Red
    Write-Host ""
    $apiKey = Read-Host "Enter your Google Gemini API Key (or press Enter to skip)"
    if ($apiKey) {
        $env:GOOGLE_API_KEY = $apiKey
        Write-Host "API Key set for this session" -ForegroundColor Green
    } else {
        Write-Host "Skipped - You can use Ollama (free) instead" -ForegroundColor Yellow
        $env:LLM_PROVIDER = "ollama"
    }
}

Write-Host ""

# Step 2: Supabase Setup
Write-Host "Step 2: Supabase Database Connection" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

if ($env:SUPABASE_URL -and $env:SUPABASE_KEY) {
    Write-Host "Supabase credentials already configured!" -ForegroundColor Green
    Write-Host "  URL: $env:SUPABASE_URL" -ForegroundColor Gray
} else {
    Write-Host "Supabase is needed for:" -ForegroundColor White
    Write-Host "  - Storing CV intelligence in a database" -ForegroundColor Gray
    Write-Host "  - Fast filtering and search" -ForegroundColor Gray
    Write-Host "  - Dashboard statistics" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Do you have a Supabase account?" -ForegroundColor White
    Write-Host "  1. Yes - I have credentials" -ForegroundColor Gray
    Write-Host "  2. No - Show me how to set up (FREE)" -ForegroundColor Gray
    Write-Host "  3. Skip for now (use local files only)" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "Enter choice (1-3)"
    
    if ($choice -eq "1") {
        Write-Host ""
        $supabaseUrl = Read-Host "Enter your Supabase URL (https://xxx.supabase.co)"
        $supabaseKey = Read-Host "Enter your Supabase anon key (starts with eyJ...)"
        
        if ($supabaseUrl -and $supabaseKey) {
            $env:SUPABASE_URL = $supabaseUrl
            $env:SUPABASE_KEY = $supabaseKey
            Write-Host "Supabase credentials set!" -ForegroundColor Green
            
            Write-Host ""
            Write-Host "Now you need to create the database table." -ForegroundColor Yellow
            Write-Host "Run this command to get the SQL:" -ForegroundColor White
            Write-Host "  python supabase_storage.py --action setup" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Then:" -ForegroundColor White
            Write-Host "  1. Copy the SQL output" -ForegroundColor Gray
            Write-Host "  2. Go to your Supabase dashboard" -ForegroundColor Gray
            Write-Host "  3. Open SQL Editor" -ForegroundColor Gray
            Write-Host "  4. Paste and run the SQL" -ForegroundColor Gray
            Write-Host ""
            
            $runSetup = Read-Host "Generate SQL setup now? (Y/N)"
            if ($runSetup -eq "Y" -or $runSetup -eq "y") {
                Write-Host ""
                python supabase_storage.py --action setup
            }
        } else {
            Write-Host "Credentials not provided. Skipping..." -ForegroundColor Yellow
        }
    }
    elseif ($choice -eq "2") {
        Write-Host ""
        Write-Host "Opening setup guide..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Please follow these steps:" -ForegroundColor White
        Write-Host "  1. Open SUPABASE_SETUP_GUIDE.md in this folder" -ForegroundColor Gray
        Write-Host "  2. Follow the step-by-step instructions" -ForegroundColor Gray
        Write-Host "  3. Come back and run this script again" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Opening guide now..." -ForegroundColor Cyan
        Start-Process "SUPABASE_SETUP_GUIDE.md"
    }
    elseif ($choice -eq "3") {
        Write-Host "Skipping Supabase - will use local JSON files" -ForegroundColor Yellow
        Write-Host "  Note: Dashboard filtering will not work without Supabase" -ForegroundColor Gray
    }
    else {
        Write-Host "Invalid choice. Skipping Supabase setup." -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 3: Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Connection Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Google API (LLM):" -ForegroundColor White
if ($env:GOOGLE_API_KEY) {
    Write-Host "  CONFIGURED (Gemini)" -ForegroundColor Green
} elseif ($env:OPENAI_API_KEY) {
    Write-Host "  CONFIGURED (OpenAI)" -ForegroundColor Green
} elseif ($env:ANTHROPIC_API_KEY) {
    Write-Host "  CONFIGURED (Anthropic)" -ForegroundColor Green
} elseif ($env:LLM_PROVIDER -eq "ollama") {
    Write-Host "  Using Ollama (FREE, local)" -ForegroundColor Green
} else {
    Write-Host "  NOT CONFIGURED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Supabase Database:" -ForegroundColor White
if ($env:SUPABASE_URL -and $env:SUPABASE_KEY) {
    Write-Host "  CONFIGURED" -ForegroundColor Green
    Write-Host "    URL: $env:SUPABASE_URL" -ForegroundColor Gray
} else {
    Write-Host "  NOT CONFIGURED (using local files)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ready to Start?" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run these commands to start:" -ForegroundColor White
Write-Host "  python app.py" -ForegroundColor Cyan
Write-Host "  # Then open: http://localhost:5000" -ForegroundColor Gray
Write-Host ""

# Step 4: Save to profile (optional)
Write-Host "Make these settings permanent?" -ForegroundColor Yellow
Write-Host "   (Add to PowerShell profile so you do not have to set them again)" -ForegroundColor Gray
Write-Host ""
$saveProfile = Read-Host "Save to profile? (Y/N)"

if ($saveProfile -eq "Y" -or $saveProfile -eq "y") {
    # Check if profile exists
    if (!(Test-Path $PROFILE)) {
        New-Item -Path $PROFILE -Type File -Force | Out-Null
        Write-Host "Created PowerShell profile" -ForegroundColor Green
    }
    
    # Backup existing profile
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "$PROFILE.backup_$timestamp"
    Copy-Item $PROFILE $backupPath -ErrorAction SilentlyContinue
    
    # Append settings
    $profileContent = "`n# === CV Intelligence System - Auto-loaded on PowerShell start ===`n"
    
    if ($env:GOOGLE_API_KEY) {
        $profileContent += "`$env:GOOGLE_API_KEY = `"$env:GOOGLE_API_KEY`"`n"
    }
    if ($env:OPENAI_API_KEY) {
        $profileContent += "`$env:OPENAI_API_KEY = `"$env:OPENAI_API_KEY`"`n"
    }
    if ($env:ANTHROPIC_API_KEY) {
        $profileContent += "`$env:ANTHROPIC_API_KEY = `"$env:ANTHROPIC_API_KEY`"`n"
    }
    if ($env:SUPABASE_URL) {
        $profileContent += "`$env:SUPABASE_URL = `"$env:SUPABASE_URL`"`n"
    }
    if ($env:SUPABASE_KEY) {
        $profileContent += "`$env:SUPABASE_KEY = `"$env:SUPABASE_KEY`"`n"
    }
    if ($env:LLM_PROVIDER) {
        $profileContent += "`$env:LLM_PROVIDER = `"$env:LLM_PROVIDER`"`n"
    }
    
    Add-Content -Path $PROFILE -Value $profileContent
    
    Write-Host "Settings saved to PowerShell profile!" -ForegroundColor Green
    Write-Host "  Profile: $PROFILE" -ForegroundColor Gray
    Write-Host "  Backup: $backupPath" -ForegroundColor Gray
    Write-Host "  These will auto-load next time you open PowerShell" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
