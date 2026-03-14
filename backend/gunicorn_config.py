"""Gunicorn configuration for production deployment.

Usage:
    gunicorn app.main:app -c gunicorn_config.py
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count())
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5

# Process naming
proc_name = "accessibleai"

# Server mechanics
daemon = False
pidfile = None
umask = 0o007
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
prepend = False

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print(f"Starting AccessibleAI with {workers} workers...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"AccessibleAI server is ready. Listening on {bind}")

def on_exit(server):
    """Called just before the master process is killed."""
    print("AccessibleAI server is shutting down...")

def worker_int(worker):
    """Called just after a worker is initialized."""
    print(f"Worker {worker.pid} initialized...")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker {worker.pid} spawned...")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Forked child, re-executing.")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker {worker.pid} exited...")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"Worker {worker.pid} aborted...")

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    print(f"Number of workers changed from {old_value} to {new_value}")
