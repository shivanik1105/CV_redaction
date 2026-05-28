# Render Deployment Troubleshooting

## Error: "Exited with status 1 while building your code"

This means the build failed. Here's how to fix it:

---

## Step 1: Check Full Build Logs

In Render dashboard:
1. Click on your service
2. Go to "Logs" tab
3. Scroll up to see the full build output
4. Look for the **first error message** (usually in red)

Common error patterns:

### Error Pattern 1: Dependency Installation Failed
```
ERROR: Could not find a version that satisfies the requirement...
```

**Fix**: Update `requirements.txt` with compatible versions

### Error Pattern 2: Python Version Issue
```
python: command not found
```

**Fix**: Render might be using wrong Python version

### Error Pattern 3: System Dependencies Missing
```
error: command 'gcc' failed
```

**Fix**: Need to install system packages

### Error Pattern 4: Memory Limit
```
Killed
```

**Fix**: Upgrade to paid plan or reduce dependencies

---

## Step 2: Quick Fixes

### Fix 1: Simplify Build Command

Update `render.yaml`:

```yaml
services:
  - type: web
    name: cv-redactor
    env: python
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt --no-cache-dir
    startCommand: gunicorn --preload --workers 1 --threads 1 --timeout 180 --bind 0.0.0.0:$PORT app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### Fix 2: Use Lighter Dependencies

Create `requirements-render.txt`:

```txt
# Core - Minimal for Render
Flask==3.0.0
Werkzeug==3.0.1
python-dotenv==1.0.0
gunicorn==21.2.0

# PDF Processing - Lightweight
pypdfium2==4.26.0
PyMuPDF==1.24.0

# Document Processing
python-docx==1.1.0
Pillow==10.0.0

# PII Detection - Minimal
presidio-analyzer==2.2.33
presidio-anonymizer==2.2.33
spacy==3.7.2
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# LLM - Only Groq (lightest)
groq==1.4.0

# Database
supabase==2.28.0
httpx==0.26.0

# Vector Search - Minimal
sentence-transformers==2.2.2
numpy==1.24.0

# Utilities
requests==2.31.0
```

Then update `render.yaml`:
```yaml
buildCommand: pip install -r requirements-render.txt --no-cache-dir
```

### Fix 3: Add System Dependencies

If you see `gcc` or compilation errors, create `render-build.sh`:

```bash
#!/bin/bash
apt-get update
apt-get install -y build-essential
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

Update `render.yaml`:
```yaml
buildCommand: bash render-build.sh
```

---

## Step 3: Test Locally First

Before deploying, test the build locally:

```bash
# Activate virtual environment
.venv\Scripts\activate

# Test installation
pip install -r requirements.txt

# If it fails locally, it will fail on Render
# Fix local issues first
```

---

## Step 4: Common Specific Fixes

### Issue: spaCy Model Download Fails

**Error**: `Can't find model 'en_core_web_sm'`

**Fix**: Change in `requirements.txt`:
```txt
# Instead of:
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Use:
spacy==3.7.2
```

Then add to `buildCommand`:
```yaml
buildCommand: |
  pip install -r requirements.txt
  python -m spacy download en_core_web_sm
```

### Issue: PyMuPDF Installation Fails

**Error**: `Failed building wheel for PyMuPDF`

**Fix**: Use pre-built wheel:
```txt
PyMuPDF==1.24.0  # Older stable version
```

### Issue: Memory Limit on Free Tier

**Error**: Build process killed

**Fix**: 
1. Upgrade to Starter plan ($7/month)
2. Or use minimal dependencies (see Fix 2 above)

---

## Step 5: Alternative Deployment Strategy

If build keeps failing, try deploying without heavy dependencies:

### Minimal Deployment (Phase 1):

1. **Remove heavy dependencies temporarily**:
   - Remove `sentence-transformers`
   - Remove `presidio-analyzer`
   - Keep only core Flask + Supabase

2. **Deploy basic version**

3. **Add dependencies one by one**

4. **Find which one causes the issue**

---

## Step 6: Check Render Service Settings

In Render dashboard:

1. **Environment**: Should be `Python`
2. **Python Version**: Should be `3.11.0` (set in env vars)
3. **Build Command**: Should match `render.yaml`
4. **Start Command**: Should match `render.yaml`

---

## Step 7: Enable Build Logs

Add this to see more details:

```yaml
buildCommand: |
  echo "Starting build..."
  pip --version
  python --version
  pip install --upgrade pip
  pip install -r requirements.txt --verbose
  echo "Build complete!"
```

---

## Quick Diagnostic Commands

Add these to your `buildCommand` to diagnose:

```yaml
buildCommand: |
  echo "=== System Info ==="
  python --version
  pip --version
  free -h
  echo "=== Installing Dependencies ==="
  pip install -r requirements.txt 2>&1 | tee build.log
  echo "=== Build Complete ==="
```

---

## Most Likely Solutions

Based on your error, try these in order:

### Solution 1: Use --no-cache-dir
```yaml
buildCommand: pip install -r requirements.txt --no-cache-dir
```

### Solution 2: Upgrade pip first
```yaml
buildCommand: |
  pip install --upgrade pip
  pip install -r requirements.txt
```

### Solution 3: Install in stages
```yaml
buildCommand: |
  pip install Flask gunicorn python-dotenv
  pip install supabase httpx
  pip install PyMuPDF pypdfium2
  pip install -r requirements.txt
```

### Solution 4: Use minimal requirements
```yaml
buildCommand: pip install -r requirements-render.txt
```

---

## Need More Help?

1. **Copy the full error message** from Render logs
2. **Share the first error** (not the last line)
3. **Check which package failed** to install
4. **Try installing that package locally** first

---

## Emergency: Deploy Without AI Features

If you need to deploy ASAP, use this minimal `requirements.txt`:

```txt
Flask==3.0.0
gunicorn==21.2.0
python-dotenv==1.0.0
supabase==2.28.0
PyMuPDF==1.24.0
python-docx==1.1.0
```

This will deploy a basic version. Add AI features later.

---

**Next Step**: Check your Render logs and find the specific error message, then apply the appropriate fix above.
