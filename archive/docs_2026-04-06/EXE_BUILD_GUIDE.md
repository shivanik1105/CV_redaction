# Building Windows .exe for CV Intelligence System

## Overview
This guide shows how to create a standalone Windows executable (.exe) that users can download and run without installing Python or any dependencies.

---

## Prerequisites

```bash
# Install PyInstaller
pip install pyinstaller

# Install all project dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## Step 1: Create Build Script

Create `build_exe.py`:

---

## Step 2: Build the Executable

### Option A: Simple Build (Recommended)

```bash
# Build using the spec file
pyinstaller build_installer.spec

# Or use the build script
python build_exe.py
```

### Option B: Manual Build

```bash
pyinstaller --onefile --windowed ^
  --name=CVIntelligence ^
  --add-data="templates;templates" ^
  --add-data="config;config" ^
  --hidden-import=presidio_analyzer ^
  --hidden-import=spacy ^
  --hidden-import=sentence_transformers ^
  --collect-all=presidio_analyzer ^
  --collect-all=spacy ^
  app_launcher.py
```

---

## Step 3: Test the Executable

```bash
# Run the exe
dist\CVIntelligence.exe

# It should:
# 1. Start Flask server
# 2. Open browser automatically
# 3. Show the CV Intelligence interface
```

---

## Step 4: Create User Package

### Create a distribution folder:

```
CVIntelligence-v1.0/
├── CVIntelligence.exe          # Main executable
├── README.txt                  # User instructions
├── .env.example                # Configuration template
├── config/                     # Configuration files
│   ├── locations.json
│   ├── pii_patterns.json
│   ├── protected_terms.json
│   ├── sections.json
│   └── text_healing.json
└── sample_cvs/                 # Sample CVs (optional)
```

---

## Step 5: Create README for Users

Create `README.txt`:

```
CV Intelligence System - User Guide
====================================

QUICK START
-----------
1. Double-click CVIntelligence.exe
2. The application will open in your browser
3. Start processing CVs!

FIRST TIME SETUP
----------------
1. Copy .env.example to .env
2. Edit .env and add your API keys:
   - GROQ_API_KEY (get from console.groq.com)
   - SUPABASE_URL (optional)
   - SUPABASE_KEY (optional)

SYSTEM REQUIREMENTS
-------------------
- Windows 10/11 (64-bit)
- 4GB RAM minimum
- 2GB free disk space
- Internet connection (for API calls)

USAGE
-----
1. Upload CVs (PDF/DOCX)
2. Optionally provide Job Description
3. Click "Process CVs"
4. Search and filter candidates

TROUBLESHOOTING
---------------
- If browser doesn't open: Go to http://localhost:5000
- If port 5000 is busy: Close other applications
- For errors: Check the console window

SUPPORT
-------
- Documentation: See COMPLETE_SYSTEM_ARCHITECTURE.md
- Issues: Contact support

VERSION: 1.0
DATE: March 2026
```

---

## Step 6: Create Installer (Optional)

### Using Inno Setup (Free)

1. Download Inno Setup: https://jrsoftware.org/isinfo.php

2. Create `installer.iss`:

```iss
[Setup]
AppName=CV Intelligence System
AppVersion=1.0
DefaultDirName={pf}\CVIntelligence
DefaultGroupName=CV Intelligence
OutputDir=installer_output
OutputBaseFilename=CVIntelligence-Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\CVIntelligence.exe"; DestDir: "{app}"
Source: ".env.example"; DestDir: "{app}"
Source: "config\*"; DestDir: "{app}\config"
Source: "README.txt"; DestDir: "{app}"

[Icons]
Name: "{group}\CV Intelligence"; Filename: "{app}\CVIntelligence.exe"
Name: "{commondesktop}\CV Intelligence"; Filename: "{app}\CVIntelligence.exe"

[Run]
Filename: "{app}\CVIntelligence.exe"; Description: "Launch CV Intelligence"; Flags: postinstall nowait skipifsilent
```

3. Compile with Inno Setup to create `CVIntelligence-Setup.exe`

---

## File Sizes

### Expected Sizes:
- **CVIntelligence.exe**: ~500-800 MB (includes all dependencies)
- **With Installer**: ~400-600 MB (compressed)

### Why so large?
- Python runtime: ~50 MB
- spaCy model: ~15 MB
- sentence-transformers: ~100 MB
- PyTorch: ~200 MB
- Other dependencies: ~100 MB

### To reduce size:
```bash
# Use UPX compression
pyinstaller --onefile --upx-dir=upx app_launcher.py

# Exclude unnecessary packages
--exclude-module=matplotlib
--exclude-module=pandas
```

---

## Distribution Options

### Option 1: Direct Download
- Upload `CVIntelligence.exe` to cloud storage
- Share download link
- Users download and run

### Option 2: Installer
- Create installer with Inno Setup
- Upload `CVIntelligence-Setup.exe`
- Users install like normal software

### Option 3: Portable ZIP
- Create ZIP with exe + config
- Users extract and run
- No installation needed

---

## Cloud Storage Options

### Free Options:
1. **Google Drive**: 15GB free
2. **Dropbox**: 2GB free
3. **OneDrive**: 5GB free
4. **GitHub Releases**: Unlimited (for open source)

### Paid Options:
1. **AWS S3**: ~₹2/GB/month
2. **Azure Blob**: ~₹2/GB/month
3. **DigitalOcean Spaces**: ₹420/month (250GB)

---

## User Instructions

### For End Users:

**Download and Run**:
```
1. Download CVIntelligence.exe
2. Double-click to run
3. Browser opens automatically
4. Start using!
```

**First Time Setup**:
```
1. Get Groq API key (free):
   - Go to console.groq.com
   - Sign up
   - Create API key
   
2. Configure:
   - Copy .env.example to .env
   - Add GROQ_API_KEY=your_key
   
3. Run CVIntelligence.exe
```

**No Python Required**:
- ✅ Everything bundled in .exe
- ✅ No installation needed
- ✅ Just download and run

---

## Troubleshooting Build Issues

### Issue: "Module not found"
```bash
# Add to hidden imports
--hidden-import=module_name
```

### Issue: "Data files missing"
```bash
# Add data files
--add-data="source;destination"
```

### Issue: "Exe too large"
```bash
# Exclude unnecessary modules
--exclude-module=matplotlib
--exclude-module=pandas
```

### Issue: "Antivirus blocks exe"
```bash
# Sign the executable (requires code signing certificate)
# Or add exception in antivirus
```

### Issue: "Slow startup"
```bash
# Use --onedir instead of --onefile
# Faster but creates folder with multiple files
```

---

## Advanced: Auto-Update System

### Create update checker:

```python
# update_checker.py
import requests
import json

def check_for_updates():
    """Check if new version available"""
    try:
        response = requests.get('https://your-server.com/version.json')
        latest = response.json()['version']
        current = '1.0'
        
        if latest > current:
            print(f"New version available: {latest}")
            print("Download from: https://your-server.com/download")
            return True
        return False
    except:
        return False
```

---

## Security Considerations

### For Distribution:
1. **Code Signing**: Sign exe with certificate (₹8,400/year)
2. **Virus Scan**: Scan exe before distribution
3. **HTTPS**: Use HTTPS for downloads
4. **Checksums**: Provide SHA256 hash

### For Users:
1. **API Keys**: Never share .env file
2. **Updates**: Only download from official source
3. **Antivirus**: Keep antivirus updated

---

## Licensing

### If Open Source:
```
Include LICENSE file
Mention dependencies and their licenses
```

### If Commercial:
```
Include EULA
Protect API keys
Consider license management
```

---

## Summary

### Build Command:
```bash
pyinstaller build_installer.spec
```

### Output:
```
dist/CVIntelligence.exe  (~500-800 MB)
```

### Distribution:
```
1. Upload to cloud storage
2. Share download link
3. Users download and run
4. No Python installation needed!
```

### User Experience:
```
1. Download exe
2. Double-click
3. Browser opens
4. Start processing CVs
```

---

**Last Updated**: March 27, 2026  
**Tested On**: Windows 10/11 (64-bit)  
**Python Version**: 3.11+
