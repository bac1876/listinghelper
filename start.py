#!/usr/bin/env python3
"""
Start script for Railway deployment
Handles PORT environment variable properly
"""
import os
import sys
import subprocess

# Get PORT from environment, default to 5000
port = os.environ.get('PORT', '5000')

# Build the gunicorn command
cmd = [
    'gunicorn',
    'main:app',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '2',
    '--timeout', '120'
]

print(f"Starting server on port {port}...")
print(f"Command: {' '.join(cmd)}")

# Execute gunicorn
sys.exit(subprocess.call(cmd))