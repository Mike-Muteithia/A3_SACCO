"""
Akiba Sacco Core - Production WSGI Configuration
Tuned for WSL 2 / Ubuntu 24.04 LTS (Memory-Safe)
"""

import os
from pathlib import Path

# Network Binding (0.0.0.0 exposes port 8000 to Windows localhost)
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
backlog = 2048

# Worker Architecture: Fixed to 2 workers for WSL 2 to prevent RAM exhaustion
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "gthread"
threads = 4
worker_connections = 1000
timeout = 60
graceful_timeout = 30
keepalive = 5

# Worker Lifecycle & Memory Recycler
max_requests = 1000
max_requests_jitter = 100
preload_app = False
proc_name = "akiba_sacco_wsgi"

# Structured Logging
log_dir = Path("/var/log/akiba_sacco")
try:
    log_dir.mkdir(parents=True, exist_ok=True)
    accesslog = str(log_dir / "gunicorn_access.log")
    errorlog = str(log_dir / "gunicorn_error.log")
except (PermissionError, OSError):
    local_log_dir = Path(__file__).resolve().parent / "logs"
    local_log_dir.mkdir(parents=True, exist_ok=True)
    accesslog = str(local_log_dir / "gunicorn_access.log")
    errorlog = str(local_log_dir / "gunicorn_error.log")

loglevel = "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sus'
capture_output = True

# Request Security Bounds
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
