#!/bin/bash
# Script de inicio que permite ejecutar API o Worker según SERVICE_TYPE

if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "Starting Worker..."
    python worker.py
else
    echo "Starting API..."
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi
