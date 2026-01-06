# Dockerfile (CW2 ProfileService)
# Builds a self-contained container image for the ProfileService API.

FROM python:3.9-bullseye

# Accept Microsoft EULA automatically (required for SQL Server ODBC driver)
# Disable Python bytecode generation and enable unbuffered output for clearer logs
ENV ACCEPT_EULA=Y
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# ---- Build-time database configuration ----
# Credentials are provided at build time and baked into the image.
ARG DB_SERVER
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_DRIVER="ODBC Driver 18 for SQL Server"

# Expose the build arguments as environment variables inside the container
ENV DB_SERVER=${DB_SERVER} \
    DB_NAME=${DB_NAME} \
    DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    DB_DRIVER=${DB_DRIVER}


# --- System dependencies ---
# Install system packages required for:
# - pyodbc
# - Microsoft SQL Server ODBC driver
# - building Python wheels with native extensions
RUN apt-get update -y \
  && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg2 \
      unixodbc unixodbc-dev odbcinst1debian2 \
      gcc g++ \
  && rm -rf /var/lib/apt/lists/*


# --- Install Microsoft SQL Server ODBC Driver ---
# Use msodbcsql18 because it supports arm64 builds (Apple Silicon) and amd64.
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
     > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update -y \
  && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
  && rm -rf /var/lib/apt/lists/*



# --- Application setup ---
WORKDIR /app

# Install Python dependencies separately to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r /app/requirements.txt

# Copy application source code
COPY . /app

# --- Security hardening ---
# Run the application as a non-root user to reduce container privileges
RUN useradd -m appuser \
  && chown -R appuser:appuser /app \
  && chmod +x /app/entrypoint.sh

USER appuser


# API listens on port 8000
EXPOSE 8000


# --- Container health check ---
# Periodically calls the existing /api/health endpoint to verify liveness.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/health || exit 1


# Entrypoint script:
# - builds/verifies the database schema
# - then launches the API
ENTRYPOINT ["./entrypoint.sh"]