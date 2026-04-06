# Step-by-Step Build Instructions

## 🚀 Quick Build (Recommended)

### Option 1: PowerShell Script
```powershell
.\build.ps1
```

### Option 2: Python Script
```powershell
python build_exe.py
```

### Option 3: Direct PyInstaller
```powershell
pyinstaller build_installer.spec
```

---

## 📋 Detailed Steps

### Step 1: Install PyInstaller

```powershell
pip install pyinstaller
```

### Step 2: Verify Installation

```powershell
pyinstaller --version
```

You should see something like: `5.13.0` or similar

### Step 3: Build the Executable

```powershell
# Use the PowerShell script
.\build.ps1

# OR use PyInstaller directly
pyinstaller build_installer.spec
```

### Step 4: Wait for Build

- Build time: 5-10 minutes
- You'll see lots of output (normal)
- Wait for "completed successfully" message

### Step 5: Find Your Executable

```powershell
# Check if it exists
Test-Path dist\CVIntelligence.exe

# Check file size
(Get-Item dist\CVIntelligence.exe).Length / 1MB
```

Expected size: 500-800 MB

### Step 6: Test the Executable

```powershell
# Run it
.\dist\CVIntelligence.exe

# Browser should open automatically
# Go to: http://localhost:5000
```

---

## 🐛 Troubleshooting

### Error: "PyInstaller not found"

```powershell
# Install it
pip install pyinstaller

# Verify
pip show pyinstaller
```

### Error: "Module not found"

```powershell
# Install all dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Error: "Cannot find spec file"

```powershell
# Make sure you're in the project directory
Get-Location

# Should show: C:\Users\shiva\Downloads\samplecvs

# List files
Get-ChildItem *.spec
```

### Error: "Build failed"

```powershell
# Clean and retry
Remove-Item -Recurse -Force dist, build
pyinstaller --clean build_installer.spec
```

### Error: "Out of memory"

```powershell
# Close other applications
# Or use --onedir instead of --onefile
# Edit build_installer.spec and change onefile=True to onefile=False
```

---

## 🔍 Verify Build Success

### Check 1: File Exists
```powershell
Test-Path dist\CVIntelligence.exe
# Should return: True
```

### Check 2: File Size
```powershell
(Get-Item dist\CVIntelligence.exe).Length / 1MB
# Should be: 500-800 MB
```

### Check 3: Run Test
```powershell
.\dist\CVIntelligence.exe
# Should start server and open browser
```

### Check 4: Process Test
```
1. Open browser: http://localhost:5000
2. Go to "Process CVs" tab
3. Click "Process All Sample CVs"
4. Should process without errors
```

---

## 📦 After Build

### Create Distribution Package

```powershell
# Create distribution folder
New-Item -ItemType Directory -Force -Path "CVIntelligence-v1.0"

# Copy files
Copy-Item "dist\CVIntelligence.exe" "CVIntelligence-v1.0\"
Copy-Item ".env.example" "CVIntelligence-v1.0\"
Copy-Item -Recurse "config" "CVIntelligence-v1.0\"

# Create README
@"
CV Intelligence System v1.0

Quick Start:
1. Get FREE API key from console.groq.com
2. Copy .env.example to .env
3. Add your API key to .env
4. Double-click CVIntelligence.exe
5. Browser opens automatically!

See USER_GUIDE.md for detailed instructions.
"@ | Out-File "CVIntelligence-v1.0\README.txt"

# Create ZIP
Compress-Archive -Path "CVIntelligence-v1.0" -DestinationPath "CVIntelligence-v1.0.zip"

Write-Host "✓ Distribution package created: CVIntelligence-v1.0.zip"
```

### Upload to Cloud

```powershell
# Option 1: Google Drive
# - Go to drive.google.com
# - Upload CVIntelligence-v1.0.zip
# - Right-click → Share → Get link

# Option 2: GitHub Release
# - Go to your GitHub repo
# - Releases → Create new release
# - Upload CVIntelligence-v1.0.zip

# Option 3: Dropbox
# - Go to dropbox.com
# - Upload CVIntelligence-v1.0.zip
# - Share → Create link
```

---

## 🎯 Quick Commands Reference

```powershell
# Build
.\build.ps1

# Test
.\dist\CVIntelligence.exe

# Check size
(Get-Item dist\CVIntelligence.exe).Length / 1MB

# Clean
Remove-Item -Recurse -Force dist, build

# Rebuild
pyinstaller --clean build_installer.spec

# Create package
Compress-Archive -Path "dist\CVIntelligence.exe" -DestinationPath "CVIntelligence.zip"
```

---

## 📊 Build Progress

### What You'll See:

```
1. "Analyzing dependencies..." (1-2 min)
2. "Collecting files..." (2-3 min)
3. "Building executable..." (2-3 min)
4. "Compressing..." (1-2 min)
5. "Build completed successfully!" (done!)
```

### Total Time: 5-10 minutes

---

## ✅ Success Checklist

- [ ] PyInstaller installed
- [ ] All dependencies installed
- [ ] Build completed without errors
- [ ] CVIntelligence.exe exists in dist/
- [ ] File size is 500-800 MB
- [ ] Exe runs without errors
- [ ] Browser opens automatically
- [ ] Can process sample CVs
- [ ] Distribution package created
- [ ] Uploaded to cloud storage
- [ ] Download link tested

---

## 🎉 You're Done!

Your executable is ready to distribute!

**Next Steps**:
1. Test thoroughly
2. Create user guide
3. Upload to cloud
4. Share with users

**Users will**:
1. Download exe
2. Get API key
3. Configure .env
4. Run and use!

**No Python needed!** ✨

---

**Need Help?**
- Build issues: Check error messages above
- PyInstaller docs: https://pyinstaller.org
- Project docs: See EXE_BUILD_GUIDE.md
