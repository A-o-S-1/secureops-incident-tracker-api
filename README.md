# SecureOps Incident Tracker API

A beginner-friendly, security-conscious REST API for recording and managing **synthetic security incidents**. Built with FastAPI, SQLAlchemy, Pydantic, Alembic, JWT bearer authentication, Argon2 password hashing, and pytest.

> **Scope:** This project records incidents entered by people or other systems. It does **not** detect attacks, inspect network traffic, or replace a SIEM, enterprise SOC, incident-response platform, or dedicated security logging service.

## Features

- Create, read, update, search, filter, and paginate incidents.
- Controlled lifecycle: `new → investigating → contained → investigating/resolved → closed`; `investigating → resolved`; `resolved → investigating` is allowed for reopening.
- Severity: `low`, `medium`, `high`, `critical`.
- Categories: `malware`, `phishing`, `unauthorized_access`, `data_exposure`, `availability`, `policy_violation`, `other`.
- JWT bearer authentication; Argon2 password hashes; role-based permissions.
- Admin-only user administration, audit-log viewing, incident deletion, and closing incidents.
- Audit entries for significant changes with an allowlisted summary that avoids credentials, tokens, and full incident descriptions.
- SQLite by default; PostgreSQL supported through `DATABASE_URL`.
- OpenAPI docs at `/docs`, alternative docs at `/redoc`.

## Architecture

```text
app/
  main.py              FastAPI app and startup
  config.py            Environment configuration
  database.py          SQLAlchemy engine/session
  models.py             User, Incident, AuditLog database models
  schemas.py            Pydantic request/response validation
  security.py           Password hashing and signed access tokens
  dependencies.py       Current-user and role checks
  audit.py              Central audit-entry helper
  routers/
    auth.py             Login and current-user endpoint
    users.py            Admin user management
    incidents.py        Incident CRUD, filters, lifecycle
    audit.py             Admin-only audit-log access
migrations/             Alembic migration environment and initial schema
scripts/                Interactive admin creation and synthetic demo seeding
tests/                  API integration tests
```

Routes are grouped by concern. Pydantic schemas are separate from database models, and authorization checks are reusable dependencies.

## Roles and permissions

| Action | Analyst | Admin |
|---|---:|---:|
| Sign in / view own profile | Yes | Yes |
| Read, search, create incidents | Yes | Yes |
| Update incident details / transition status | Yes, subject to lifecycle rules | Yes |
| Close an incident | No | Yes |
| Delete incidents | No | Yes |
| Create/list/deactivate users | No | Yes |
| Read audit logs | No | Yes |

Any authenticated analyst or administrator can create and view incidents. A closed incident can only be edited by an admin; deletion is admin-only. Admins cannot deactivate their own account through the API.

## Incident lifecycle

- `new`: captured and awaiting triage.
- `investigating`: assigned for analysis.
- `contained`: immediate impact is believed to be limited.
- `resolved`: remediation is considered complete; resolution notes are required.
- `closed`: administratively closed; terminal in the normal workflow.

Allowed transitions are enforced by the API. Invalid transitions return HTTP `409`; attempts to resolve without notes return `422`. Reopening a resolved incident to `investigating` is allowed. `closed` is terminal.

## API endpoints

All endpoints except `GET /health` and `POST /auth/token` require `Authorization: Bearer <access_token>`.

| Method | Endpoint | Purpose / access |
|---|---|---|
| GET | `/health` | Health check, public |
| POST | `/auth/token` | OAuth2 password form login |
| GET | `/auth/me` | Current account |
| POST | `/users` | Create user, admin |
| GET | `/users` | List users, admin |
| PATCH | `/users/{user_id}/deactivate` | Deactivate user, admin |
| POST | `/incidents` | Create incident, analyst/admin |
| GET | `/incidents` | Search/filter/page incidents |
| GET | `/incidents/{reference_id}` | Retrieve one incident |
| PATCH | `/incidents/{reference_id}` | Update incident fields |
| PATCH | `/incidents/{reference_id}/status` | Lifecycle transition |
| DELETE | `/incidents/{reference_id}` | Delete incident, admin |
| GET | `/audit-logs?limit=100` | Read audit events, admin |

Incident list query parameters: `q`, `severity`, `status`, `category`, `page` (starts at 1), `page_size` (1–100). Example: `/incidents?q=phishing&severity=high&page=1&page_size=10`.

### Example request

```json
{
  "title": "Synthetic suspicious login pattern",
  "description": "Training scenario for a fictional lab account; no real user data.",
  "category": "unauthorized_access",
  "severity": "high",
  "source": "demo-auth-monitor"
}
```

Create with `POST /incidents`. The API generates the `reference_id`, status, and timestamps. Example responses and the interactive Try it out tool are available in `/docs`.

## Authentication and security controls

- Passwords are hashed with Argon2 using `argon2-cffi`; plaintext passwords are never stored.
- JWT access tokens are signed with a configurable secret and expire after 30 minutes by default.
- Login failures use a generic response; protected endpoints validate token and active-user status.
- Role checks are applied to protected operations.
- Pydantic validates field lengths and enum-like fields. Pagination has bounds.
- SQLAlchemy parameterizes normal ORM queries; unique constraints protect usernames and incident references.
- Audit detail payloads are intentionally allowlisted and omit passwords, bearer tokens, full descriptions, and resolution notes.
- Secrets come from environment configuration. `.env` is excluded from Git.
- CORS is disabled unless exact origins are configured.

**Important limitations:** This is a portfolio/demo baseline, not a production security certification. The database audit table is not tamper-proof: a database owner can alter or delete it. For stronger audit assurance, export events to a separately administered append-only destination. Production deployments should also add TLS, rate limiting, monitoring, secret management, backup/restore testing, account lockout or abuse controls, and a formal threat model. Avoid storing real incident evidence or personal data in a public demo.

## Local installation (Windows 10 Command Prompt)

Install Python 3.11 or newer. From a fresh clone, open Command Prompt in the repository folder.

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Generate a random secret and place it in `.env` as `SECRET_KEY`:

```bat
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep the generated value private. The placeholder secret in `.env.example` is only for local setup and **must be replaced** before running outside a throwaway demo.

### Database and initial administrator

For local development, SQLite is the default. Apply the initial migration:

```bat
alembic upgrade head
```

Create the first admin interactively. The password is hidden while typing and is not passed in command history:

```bat
python -m scripts.create_admin
```

Do not commit the `.env` file, real credentials, or the generated SQLite database. Create more users after login using the admin-only `POST /users` endpoint.

### Run the API and load demo data

```bat
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. In another Command Prompt, activate the environment and run:

```bat
python -m scripts.seed_demo
```

Demo incidents use fictional descriptions and synthetic source names. The seed script does not create accounts or include real people. Run it only in a development/demo environment.

### Authenticate and use the API

In Swagger, use `POST /auth/token`. The login form uses `username` and `password`; copy the returned access token into **Authorize** as a bearer token. Then create, filter, and update incidents.

Using curl (available on current Windows versions):

```bat
curl -X POST http://127.0.0.1:8000/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=YOUR_ADMIN&password=YOUR_PASSWORD"
curl http://127.0.0.1:8000/incidents -H "Authorization: Bearer YOUR_TOKEN"
```

Do not paste real passwords or tokens into public terminals, issue trackers, or screenshots. Replace placeholders locally.

## Tests

Tests use an isolated SQLite file named `test_secureops.db` and create test accounts with test-only credentials.

```bat
pytest -q
```

On a fresh environment, the expected output is a pass summary. Report the actual output from your environment; do not treat an expected result as a run result.

## Migrations

The repository includes an initial Alembic migration. After changing SQLAlchemy models, generate a new migration:

```bat
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

For a production database, take a backup and review generated migrations before applying them. The demo app also calls `create_all` at startup to make first-run demos easy; for controlled deployments, apply migrations before starting the service and consider removing this fallback.

## PostgreSQL

Install PostgreSQL and create a dedicated database/user. Set a URL in `.env`, for example:

```env
DATABASE_URL=postgresql+psycopg://secureops_user:URL_ENCODED_PASSWORD@localhost:5432/secureops
```

URL-encode special characters in the password. Use a least-privilege database account and do not expose the database port publicly. Run `alembic upgrade head` after setting the environment.

## GitHub publishing

1. Create an empty GitHub repository named `secureops-incident-tracker-api`.
2. Confirm `.env`, `*.db`, and `.venv/` are not staged.
3. From the project directory:

```bat
git init
git add .
git status
git commit -m "Build SecureOps Incident Tracker API"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/secureops-incident-tracker-api.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your actual username. The URL above is a template, not a claim that a repository exists. Add a short project description and topics such as `fastapi`, `python`, `security`, `rest-api`, and `incident-management`. Never publish tokens, `.env`, test databases, or real incident information.

## Deployment guide

The application supports PostgreSQL via `DATABASE_URL` and can run with Uvicorn. A typical deployment flow is:

1. Choose a Python-capable host that currently supports web services and managed PostgreSQL.
2. Set `DATABASE_URL`, a freshly generated `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `ENVIRONMENT=production` as host-managed secrets/environment variables.
3. Configure a start command such as `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (adapt `$PORT` syntax to the host).
4. Run `alembic upgrade head` as a release/pre-deploy command where supported.
5. Create the first admin through a secure one-off console/job, not through a public bootstrap endpoint.
6. Configure HTTPS, exact CORS origins if needed, backups, log retention, and alerting. Verify the provider's current pricing, free-tier limits, sleep behavior, region availability, and database persistence before choosing a host; those details change frequently.

A practical first deployment is a small Python web service plus managed PostgreSQL. Do not assume a free tier is durable or always-on. Never use SQLite on an ephemeral filesystem for a deployed service. Deployment was not performed as part of this repository build.

## Future improvements

- Rate limiting and account lockout protections.
- Refresh-token/session revocation and token rotation.
- Structured operational logging with secret redaction.
- Dedicated append-only audit export and retention policy.
- More granular permissions, assignment workflow, and notifications.
- Integration adapters for alert sources, with authenticated ingestion and replay protection.
- CI workflow, coverage reporting, and container packaging after the core API is understood.

## License

MIT; add a `LICENSE` file if you choose to publish under that license.
