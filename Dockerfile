# Dockerfile (CW2 ProfileService)
FROM python:3.9-bullseye

ENV ACCEPT_EULA=Y
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---- Build-time DB credentials (NOT stored in repo) ----
ARG DB_SERVER
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_DRIVER="ODBC Driver 17 for SQL Server"

# Bake into the image so container can run with zero input
ENV DB_SERVER=${DB_SERVER} \
    DB_NAME=${DB_NAME} \
    DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    DB_DRIVER=${DB_DRIVER}

# --- System deps for pyodbc + MS SQL ODBC driver ---
RUN apt-get update -y \
  && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg2 \
      unixodbc unixodbc-dev odbcinst1debian2 \
      gcc g++ \
  && rm -rf /var/lib/apt/lists/*

# Add Microsoft package repo + install msodbcsql17 (Debian 11 / bullseye)
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg \
  && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" \
     > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update -y \
  && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
  && rm -rf /var/lib/apt/lists/*

# --- App setup ---
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Non-root user (OWASP-friendly) + entrypoint executable
RUN useradd -m appuser \
  && chown -R appuser:appuser /app \
  && chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

# Optional: health check (uses your existing endpoint)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
