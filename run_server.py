"""
Production Server for CV Redaction Tool
Uses Waitress (production-grade WSGI server for Windows)

HOW TO START:
    python run_server.py

HOW TO STOP:
    Press Ctrl+C in this terminal

ACCESS:
    - On THIS computer: http://localhost:5000
    - From ANY computer on the same network: http://<YOUR-IP>:5000
      Find your IP by running: ipconfig (look for IPv4 Address)
"""

import os
import socket
import logging
from waitress import serve
from app import app

# ─── Configuration ────────────────────────────────────────────────────────────
HOST = "0.0.0.0"   # Accept connections from all network devices
PORT = 5000
THREADS = 8        # Handle 8 recruiters uploading simultaneously


def get_local_ip():
    """Get this machine's local network IP so recruiters know the URL."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "YOUR-PC-IP"


# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Start Server ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    local_ip = get_local_ip()

    print("=" * 60)
    print("  CV REDACTION TOOL — PRODUCTION SERVER")
    print("=" * 60)
    print(f"  Status   : RUNNING")
    print(f"  Threads  : {THREADS} (handles {THREADS} recruiters at once)")
    print(f"  Local URL: http://localhost:{PORT}")
    print(f"  Network  : http://{local_ip}:{PORT}  ← share with recruiters")
    print("=" * 60)
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)

    # Waitress is production-grade: no debug warnings, handles concurrency
    serve(
        app,
        host=HOST,
        port=PORT,
        threads=THREADS,
        # Increase timeouts for large CV batch uploads
        channel_timeout=120,
        cleanup_interval=30,
    )
