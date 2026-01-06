#!/usr/bin/env bash
# Entrypoint script for the CW2 ProfileService container.
# Responsible for preparing the database and then starting the API.

set -e  # Exit immediately if any command fails


echo "Starting CW2 ProfileService..."

# Database credentials are expected to already be present in the container
# environment (baked in at image build time for CW2 constraints).
# If credentials are missing or invalid, build_database.py will fail fast.
echo "Running database build/verification..."
python build_database.py


# Once the database is verified, start the API process.
# 'exec' replaces the shell with the Python process so signals
# (e.g. SIGTERM) are forwarded correctly in Docker.
echo "Launching API..."
exec python app.py