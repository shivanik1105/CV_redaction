"""
Production server for the CV Redaction Pipeline (redact-only).
Uses Waitress WSGI server — safe for multiple simultaneous users.

Usage:
    python redact_server.py

Recruiters on the same network can access via:
    http://<this-machine-IP>:5000
"""

import socket
from waitress import serve
from redact_app import app

HOST    = "0.0.0.0"
PORT    = 5000
THREADS = 20  # simultaneous requests; increase for more concurrent users

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("=" * 55)
    print("  CV Redaction Pipeline — Production Server")
    print("=" * 55)
    print(f"  Local:    http://localhost:{PORT}")
    print(f"  Network:  http://{local_ip}:{PORT}")
    print(f"  Threads:  {THREADS}")
    print("  Press Ctrl+C to stop")
    print("=" * 55)

    serve(app, host=HOST, port=PORT, threads=THREADS, channel_timeout=120)
