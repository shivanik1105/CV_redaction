# Redis Setup for Windows

## Option 1: Memurai (Recommended for Windows)

Memurai is a Redis-compatible server for Windows.

### Installation:
1. Download from: https://www.memurai.com/get-memurai
2. Run the installer
3. Start Memurai service:
   ```powershell
   net start Memurai
   ```

### Configuration:
- Default port: 6379
- No password by default
- Compatible with all Redis clients

---

## Option 2: Redis via WSL (Ubuntu)

### Install Ubuntu on WSL:
```powershell
wsl --install Ubuntu
```

### Install Redis in Ubuntu:
```bash
sudo apt update
sudo apt install redis-server -y
```

### Start Redis:
```bash
sudo service redis-server start
```

### Check Status:
```bash
redis-cli ping
# Should return: PONG
```

---

## Option 3: Docker (If Docker Desktop installed)

### Run Redis Container:
```powershell
docker run -d -p 6379:6379 --name redis redis:latest
```

### Check Status:
```powershell
docker ps
```

### Stop Redis:
```powershell
docker stop redis
```

---

## Option 4: Redis for Windows (Unofficial)

### Download:
- GitHub: https://github.com/tporadowski/redis/releases
- Download: Redis-x64-5.0.14.1.msi

### Install:
1. Run the MSI installer
2. Redis will start automatically as a Windows service

### Verify:
```powershell
redis-cli ping
# Should return: PONG
```

---

## Testing Redis Connection

Once Redis is running, test the connection:

```powershell
# Test with Python
python -c "from redis import Redis; r = Redis(host='localhost', port=6379); print('✅ Redis connected:', r.ping())"
```

---

## Starting the Queue System

Once Redis is running:

### Terminal 1: Start Celery Worker
```powershell
celery -A celery_worker worker --loglevel=info --pool=solo
```

### Terminal 2: Start Flask App
```powershell
python app.py
```

### Terminal 3: Monitor Queue
Open browser: http://localhost:5000/queue-monitor

---

## Current Status

❌ Redis not installed
✅ Embeddings generated (7 candidates)
⚠️ Supabase paused (using local fallback)

**Recommendation:** Install Memurai or Redis via WSL for full queue functionality.

For now, the application works in synchronous mode without Redis.
