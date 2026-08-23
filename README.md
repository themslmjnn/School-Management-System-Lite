# School Management System — Lite

A production-grade REST API for managing a school's staff, students, groups, and subjects. Built
as a focused, complete backend project demonstrating real-world engineering patterns: advisory
locking, outbox-based email delivery, rotating refresh tokens with family tracking, and structured
observability.

This is the Lite edition — intentionally scoped to the user management and school structure
layer, without academics, grades, or guardian functionality. Those are the domain of
Meridian AMS, its full-scale successor.

## Features

**Authentication & Security**
- JWT access tokens with per-user versioning for instant server-side invalidation
- Rotating refresh tokens stored as bcrypt hashes with family tracking — reuse of a revoked token
  invalidates the entire family, detecting token theft
- HttpOnly, Secure, SameSite=Strict cookie handling for refresh tokens
- Account lockout after repeated failed login attempts
- Forgot password and admin-initiated password reset flows
- Email change confirmation via a short-lived verification code

**User Management**
- Four roles: System Admin, Director, Teacher, Student
- System Admin controls all user registration — no self-registration
- Full account lifecycle: invite → activation → active → deactivated / graduated / expelled /
  withdrawn
- Contact uniqueness enforced across roles: staff and directors hold unique phone and email;
  up to three students may share the same contact (family use case)
- PostgreSQL advisory locks prevent race conditions on concurrent student registrations sharing
  contact information — a gap that partial unique indexes alone cannot close
- Invite token and reset token flows use hashed tokens; raw values are never stored

**School Structure**
- Groups with academic year, grade level, and capacity; students are assigned to a group
- Subjects with code uniqueness and archive/restore lifecycle
- Directors have read access to teachers, students, groups, and subjects

**Email Infrastructure**
- Outbox pattern: emails are written to a `pending_emails` table within the same transaction as
  the triggering operation, preventing silent loss on application crash
- Background worker polls the outbox, sends via configured provider, and tracks retry count and
  last error per email
- System Admin can view email history and manually retry failed deliveries

**Observability**
- Structured JSON logging via structlog — all log events are snake_case keys with consistent shape
- Per-request correlation IDs injected by middleware and included in every log event
- Separate liveness (`/health/live`) and readiness (`/health/ready`) endpoints; readiness checks
  both PostgreSQL and Redis with timeouts and returns 503 if either is unhealthy
- Startup validation of all config values via Pydantic Settings — the app refuses to start with
  missing or invalid configuration

**Infrastructure**
- Docker Compose with three services: application, PostgreSQL 18, Redis 8
- Health-checked service dependencies — the app waits for the database to be ready before starting
- Alembic migration history from initial schema through all cleanup migrations
- IP-based rate limiting via slowapi
- Redis caching on frequently read user and entity detail endpoints with explicit cache
  invalidation on mutation

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.135 |
| ORM | SQLAlchemy 2.0 async |
| Database | PostgreSQL 18 |
| Cache / Rate limiting | Redis 8 |
| Migrations | Alembic |
| Auth | python-jose (JWT) · passlib / bcrypt |
| Validation | Pydantic v2 · phonenumbers |
| Email | aiosmtplib / Resend |
| Logging | structlog |
| Testing | pytest-asyncio · httpx · pytest-mock |
| Linting / Typing | Ruff · mypy |
| Container | Docker · Docker Compose |

## Project Structure

src/
├── api/health.py               # Liveness + readiness endpoints
├── auth/                       # Login, logout, refresh, activation, password flows
├── core/                       # Config, DB, Redis, security, middleware, pagination,
│                               # advisory locks, rate limiting, caching
├── emails/                     # PendingEmail model, outbox service, admin email endpoints
├── groups/                     # Group CRUD with archive/restore; system admin + director access
├── subjects/                   # Subject CRUD with archive/restore; system admin + director access
├── users/
│   ├── models/                 # User, UserSession, UserActivation, UserLoginLockout
│   ├── repositories/           # Base queries, admin queries, sorting, pagination
│   ├── routers/                # system_admin, director, shared (self-service)
│   ├── services/               # system_admin, director, shared
│   └── utils/                  # Contact limit checks, constants, exception hierarchy
├── workers/
│   └── email_worker.py         # Background outbox polling worker
└── utils/                      # Enums, validators, base exceptions, helpers, cache keys

## API Overview

| Module | Endpoints | Access |
|---|---|---|
| Auth | Login, logout, refresh token, activate account, forgot password, reset password | Public / authenticated |
| Users — Admin | Register, update profile, update credentials, activate, deactivate, password reset request, resend invite, list/get teachers, list/get students | System Admin |
| Users — Director | List/get teachers, list/get students | Director |
| Users — Shared | Get my profile, update my profile, update my credentials, update my password, confirm email change, get my student profile | Any authenticated user |
| Subjects | Create, update, archive, restore, list, get by ID | System Admin (write) · Director (read) |
| Groups | Create, update, archive, restore, list, get by ID | System Admin (write) · Director (read) |
| Emails | List emails, get by ID, retry failed | System Admin |
| Health | Liveness, readiness | Public |

## Engineering Decisions

**Advisory locking for student contact uniqueness**

Students in a school may share phone numbers and email addresses — up to three students per
contact value, to accommodate siblings sharing a parent's contact details. A partial unique index
handles the single-contact case for staff, but the concurrent insert case for students (check
count → insert, with another request doing the same simultaneously) cannot be solved with indexes
alone. PostgreSQL advisory locks (`pg_advisory_xact_lock`) are acquired at the top of the
transaction, before any count check, in a consistent order (phone first, email second) to prevent
deadlocks.

**Refresh token family tracking**

Each refresh token rotation issues a new token and records a `refresh_token_family` identifier.
If a token from a previous rotation is presented — indicating the token was stolen and the thief
rotated it before the legitimate user could — the entire family is invalidated. This forces both
parties to re-authenticate and surfaces the security event in the logs.

**Access token versioning**

A per-user `access_token_version` is stored in PostgreSQL and cached in Redis. The version is
embedded in the JWT at issuance and validated on every protected request. Incrementing the version
— on deactivation, credential change, or logout — immediately invalidates all outstanding access
tokens without waiting for JWT expiry.

**Outbox pattern for email delivery**

Emails are written to a `pending_emails` table in the same database transaction as the operation
that triggers them. A background worker polls the table, sends via the configured provider, and
updates status. This means an application crash between "user registered" and "email sent" cannot
produce a user who never receives their invite — the email row survives the crash and is picked up
on the next poll cycle.

**Structured logging**

Every log event is a snake_case key (`"user_registered"`, `"login_failed"`) with typed key-value
context, not a freeform string. A request-ID middleware injects a correlation ID into every
request, and structlog binds it to all log events emitted within that request's lifecycle. This
makes tracing a specific request through the logs mechanical rather than manual.

## Running Locally

**Prerequisites:** Docker and Docker Compose.

- git clone https://github.com/themslmjnn/School-Management-System-Lite.git
- cd School-Management-System-Lite

- cp .env.example .env
# Fill in .env with your values

- make up        # Start app, PostgreSQL, and Redis
- make migrate   # Run Alembic migrations
- make logs      # Tail application logs

The API will be available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs` (development only).

**Makefile targets**

| Command | Action |
|---|---|
| `make up` | Build and start the full stack |
| `make down` | Stop and remove containers |
| `make migrate` | Run `alembic upgrade head` inside the running container |
| `make logs` | Tail application logs |
| `make format` | Run Ruff formatter |
| `make lint` | Run Ruff linter |
| `make typecheck` | Run mypy |

---

## Running Tests

Tests require a running PostgreSQL and Redis instance. The test suite targets a dedicated test
database and will refuse to run if `ENVIRONMENT` is not set to `"test"` — this prevents
accidentally running destructive schema operations against a real database.

pytest

The suite covers tests across auth, users, subjects, groups, and emails modules, split
into unit tests (service logic with mocked dependencies) and integration tests (full HTTP request
through the stack with a real test database and transaction rollback between tests).

---

## What's Not Here

This is a Lite release. The following are explicitly out of scope:

- **Academics module** — teaching assignments, student subject enrollments, head-of-class
- **Grades module** — grade records and history
- **Guardian module** — parent accounts, guardian-student links
- **Frontend** — this is a pure backend API

These are implemented in Meridian AMS, built as a ground-up redesign with a more
sophisticated user architecture, full academics coverage, CI/CD, and deployment.