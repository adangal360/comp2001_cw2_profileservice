#!/usr/bin/env bash
set -e

echo "Starting CW2 ProfileService..."

# DB creds should already be present in the image (baked at build time)
# build_database.py will raise a clear error if DB_PASSWORD is missing.
echo "Running database build/verification..."
python build_database.py

echo "Launching API..."
exec python app.py
