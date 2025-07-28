"""
🤖 Gunicorn Konfigürasyonu - KirveHub Bot
DigitalOcean Ubuntu Production Environment için optimize edilmiş
"""

import multiprocessing
import os
from pathlib import Path

# Server Settings
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout Settings
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process Naming
proc_name = "kirvehub_bot"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
worker_tmp_dir = "/dev/shm"
worker_exit_on_app = True

# SSL (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

def when_ready(server):
    """Server hazır olduğunda çalışır"""
    server.log.info("🚀 KirveHub Bot Gunicorn server hazır!")

def on_starting(server):
    """Server başlarken çalışır"""
    server.log.info("🔄 KirveHub Bot başlatılıyor...")

def on_exit(server):
    """Server kapanırken çalışır"""
    server.log.info("🛑 KirveHub Bot kapatılıyor...")

def worker_int(worker):
    """Worker interrupt olduğunda çalışır"""
    worker.log.info("⚠️ Worker interrupt edildi")

def pre_fork(server, worker):
    """Worker fork edilmeden önce çalışır"""
    server.log.info(f"🔄 Worker {worker.pid} fork ediliyor...")

def post_fork(server, worker):
    """Worker fork edildikten sonra çalışır"""
    server.log.info(f"✅ Worker {worker.pid} başlatıldı")

def post_worker_init(worker):
    """Worker initialize edildikten sonra çalışır"""
    worker.log.info(f"🎯 Worker {worker.pid} initialize edildi") 