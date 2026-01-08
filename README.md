# COMP2001 CW2 — ProfileService (Trail App Microservice)

This repository contains the **ProfileService** microservice for COMP2001 CW2.

The service is implemented in **Python (Flask + Connexion)**, uses a **Microsoft SQL Server** backend (schema `CW2`), and is deployed as a **Docker container**.  
The API is documented via **Swagger/OpenAPI** and returns **JSON**.

> **Important:** This service is designed to be pulled and run directly from Docker Hub.

---

## 1) What this microservice does

ProfileService is responsible for Trail App user profiles and preferences:

- **Profiles:**
  - CRUD operations are implemented via **SQL Server stored procedures**
  - API endpoints call stored procedures (no dynamic inline SQL for profile CRUD)

- **Activities + Favourite Activities (preferences metadata):**
  - Activities represent **user preferences** (e.g., Running, Swimming)
  - Managed via **ORM (SQLAlchemy)** (not assessed as the main resource)
  - Favourites are stored in the link table `CW2.FavouriteActivity`

- **Microservice boundaries:**
  - No Trail data duplication (this service does not store Trail details)

---

## 2) Tech Stack

- Python 3.9
- Flask + Connexion (Swagger UI)
- SQLAlchemy + Flask-SQLAlchemy
- Marshmallow (serialization)
- pyodbc + Microsoft ODBC Driver 18 for SQL Server
- Docker (containerized deployment)

---

## 3) Database requirements (CW2)

- Database hosted at: `dist-6-505.uopnet.plymouth.ac.uk`
- All DB objects live under schema: `CW2`
- All schema/tables/views/stored procedures are created by executing SQL from Python at container startup

### Objects created/verified by `build_database.py`
**Tables**
- `CW2.Profile`
- `CW2.Activity`
- `CW2.FavouriteActivity`
- `CW2.ProfileAudit`

**Stored Procedures (Profile CRUD)**
- `CW2.usp_Profile_Create`
- `CW2.usp_Profile_ReadAll`
- `CW2.usp_Profile_ReadByEmail`
- `CW2.usp_Profile_Update`
- `CW2.usp_Profile_Delete`

**Trigger**
- `CW2.trg_Profile_Audit_Insert` (audits profile creation to `CW2.ProfileAudit`)

**View**
- `CW2.vw_ProfileFavourites` (report-friendly join of profiles + favourites + activities)

**Seed data**
- Seeds baseline Profiles, Activities, and Favourites for testing.

---

## 4) Authentication & Authorisation

Authentication is performed against the COMP2001 **Authenticator API** using these headers:

- `X-Auth-Email`
- `X-Auth-Password`

### Access rules
- **Admin:** can access broader resources (e.g., list all profiles, create activities)
- **User:** can only access/modify their own profile and favourites

### Unauthenticated endpoints (CW2 onboarding exception)
- `POST /api/profiles` (first-time onboarding)
- `POST /api/auth/verify`
- `GET /api/activities`
- Health endpoints (`/api/health`, `/api/db-health`)

---

## 5) Password handling (security)

- Passwords are stored in the `CW2.Profile` table as **secure hashes only**
- Passwords are:
  - never returned in API responses
  - never logged
  - never exposed in the OpenAPI responses

Hashing is performed at the API boundary using `werkzeug.security.generate_password_hash(...)` before data is passed to stored procedures.

---

## 6) OWASP / security notes (selected)

This service includes mitigations aligned with common OWASP Top 10 risks:

- **Broken access control:** enforced via `require_admin()` and `require_self_or_admin()`
- **Injection:** Profile CRUD uses stored procedures (no dynamic SQL concatenation)
- **Insecure design / auth issues:** onboarding endpoint prevents role escalation; role changes are Admin-only

---

## 7) API Documentation (Swagger UI)

Once running:
- Swagger UI: `http://localhost:8000/api/ui`
- Base API path: `/api`

---

## 8) Docker Hub image

**Docker Hub repository:**  
`anubhavdangal/comp2001-cw2-profileservice:latest`

**Platform support:**  
This image is published as a **multi-architecture Docker image** and supports both:
- `linux/amd64`
- `linux/arm64`

### Platform compatibility note

During development, the Docker image was initially built on an Apple Silicon (ARM64) environment.  
As a result, the earliest image build was architecture-specific and did not run on some `linux/amd64`
machines (e.g. standard Windows or Intel-based systems).

To resolve this and ensure **compatibility across all machines**, the final submitted image
was rebuilt and published as a **multi-architecture Docker image**, supporting both:

- `linux/amd64` (Windows / Intel / most lab machines)
- `linux/arm64` (Apple Silicon)

Docker automatically selects the correct image variant at pull time.

---

## 9) How to run

### Pull and run the container
```bash
docker pull anubhavdangal/comp2001-cw2-profileservice:latest
docker run --rm -p 8000:8000 anubhavdangal/comp2001-cw2-profileservice:latest
