# CV Intelligence System - Deployment Guide for Teams

## 🎯 Deployment Options

We provide **3 deployment options** for your team:

1. **Docker (Recommended)** - Easiest, works everywhere
2. **Standalone Executable** - No Python needed
3. **Manual Setup** - Full control

---

## Option 1: Docker Deployment (Recommended) 🐳

### Why Docker?
- ✅ Works on Windows, Mac, Linux
- ✅ No Python installation needed
- ✅ All dependencies included
- ✅ Easy to share with team
- ✅ Consistent environment

### Prerequisites
- Docker Desktop installed
- 4GB RAM minimum
- 10GB disk space

### Quick Start

```bash
# 1. Clone repository
git clone <your-repo-url>
cd cv-intelligence-system

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Build and run
docker-compose up -d

# 4. Access application
http://localhost:5000
```

### Files Needed
- `Dockerfile`
- `docker-compose.yml`
- `.env`
- All project files

---

## Option 2: Standalone Executable (Windows) 💻

### Why Executable?
- ✅ No Python installation
- ✅ Double-click to run
- ✅ Easy for non-technical users
- ✅ Portable

### Prerequisites
- Windows 10/11
- 4GB RAM minimum
- 2GB disk space

### Quick Start

```bash
# 1. Download release package
cv-intelligence-system-v2.2-windows.zip

# 2. Extract to folder
C:\CVIntelligence\

# 3. Configure
Edit config.ini with your API keys

# 4. Run
Double-click: start-cv-system.exe

# 5. Access application
http://localhost:5000
```

### Building Executable (For Developers)

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
python build_executable.py

# Output: dist/cv-intelligence-system.exe
```

---

## Option 3: Manual Setup (Development) 🛠️

### Prerequisites
- Python 3.11+
- pip
- 4GB RAM minimum

### Quick Start

```bash
# 1. Clone repository
git clone <your-repo-url>
cd cv-intelligence-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run application
python app.py

# 6. Access application
http://localhost:5000
```

---

