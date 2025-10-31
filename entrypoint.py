#!/usr/bin/env python3
"""
Entrypoint script that starts either the API or the Worker
based on the SERVICE_TYPE environment variable.
"""
import os
import sys
import subprocess

def main():
    service_type = os.getenv('SERVICE_TYPE', 'api').lower()
    port = os.getenv('PORT', '8000')

    if service_type == 'worker':
        print("Starting Worker...", flush=True)
        sys.exit(subprocess.call(['python', 'worker.py']))
    else:
        print(f"Starting API on port {port}...", flush=True)
        sys.exit(subprocess.call([
            'uvicorn',
            'app.main:app',
            '--host', '0.0.0.0',
            '--port', port
        ]))

if __name__ == '__main__':
    main()
