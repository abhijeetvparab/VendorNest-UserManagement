"""
Start all VendorNest microservices.
    python start_all.py
"""
import subprocess
import sys
import os
import time

BASE = os.path.dirname(__file__)

services = [
    ("Auth Service    ", [sys.executable, "-m", "uvicorn", "auth_service.main:app",   "--host", "0.0.0.0", "--port", "8001"]),
    ("User Service    ", [sys.executable, "-m", "uvicorn", "user_service.main:app",   "--host", "0.0.0.0", "--port", "8002"]),
    ("Vendor Service  ", [sys.executable, "-m", "uvicorn", "vendor_service.main:app", "--host", "0.0.0.0", "--port", "8003"]),
    ("API Gateway     ", [sys.executable, "-m", "uvicorn", "api_gateway.main:app",    "--host", "0.0.0.0", "--port", "8000"]),
]

procs = []
for name, cmd in services:
    p = subprocess.Popen(cmd, cwd=BASE)
    procs.append(p)
    print(f"[START] {name} PID={p.pid}")
    time.sleep(0.5)

print("\nAll services started.")
print("  Auth    -> http://localhost:8001/docs")
print("  Users   -> http://localhost:8002/docs")
print("  Vendors -> http://localhost:8003/docs")
print("  Gateway -> http://localhost:8000/docs")
print("\nPress Ctrl+C to stop all.\n")

try:
    for p in procs:
        p.wait()
except KeyboardInterrupt:
    print("\nStopping all services...")
    for p in procs:
        p.terminate()
