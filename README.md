# Library Management Backend (Intern Starter)

Half-baked FastAPI + MongoDB library API used as a **reference implementation** for interns. This service preserves the HTTP contract of the Java starter: the same routes, status codes, JSON field names, roles, and seed data.

Only a few vertical slices are fully implemented. Everything else—especially the **Author** resource—is intentionally missing so interns can design schema, APIs, tests, and docs from the ground up while copying the existing patterns.

## What is already implemented

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/api/v1/users` | Public | Register a `MEMBER` account |
| `POST` | `/api/v1/auth/login` | Public | Issue a JWT access token |
| `PUT` | `/api/v1/books/{id}` | `ADMIN` or `LIBRARIAN` | Update an existing book |

Supporting pieces included:

- Layered architecture: router → service → repository
- Pydantic validation on request models
- Centralized API error responses
- JWT bearer authentication with role-based access
- Startup migrations for indexes + seed data
- Unit tests and Testcontainers integration tests
- OpenAPI / Swagger UI
- Docker Compose runtime (API + MongoDB)

## What is intentionally incomplete

- **Author** resource: no collection, model, repository, API, or migration. Interns own this end-to-end.
- Book create/list/get/delete
- Loan / borrow / return workflows
- User admin APIs (list, role changes, disable)
- Refresh tokens, password reset, email verification

Each remaining capability is specified in [docs/tasks/README.md](docs/tasks/README.md). See [docs/intern-roadmap.md](docs/intern-roadmap.md) for the suggested pace.

## Architecture

```text
Client
  │
  ▼
user / auth / book routers
  │
  ▼
UserService / AuthService / BookService + JwtService
  │
  ▼
UserRepository / BookRepository
  │
  ▼
MongoDB (users, books)  ← startup change units
```

Package layout under `app/`:

- `auth` — login, JWT middleware/service, security principal
- `user` — registration slice
- `book` — update slice
- `api` / `exception` — shared error model
- `migration` — index + seed change units
- `health` — `/actuator/health` and `/actuator/info`

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Optional for local IDE runs: Python 3.12+

## Quick start (Docker only)

```bash
cp .env.example .env
docker compose up --build
```

Services:

- API: [http://localhost:8080](http://localhost:8080)
- Health: [http://localhost:8080/actuator/health](http://localhost:8080/actuator/health)
- Swagger UI: [http://localhost:8080/swagger-ui.html](http://localhost:8080/swagger-ui.html)
- OpenAPI JSON: [http://localhost:8080/v3/api-docs](http://localhost:8080/v3/api-docs)
- MongoDB: `localhost:27017` / database `library_management`

Seeded admin (override via `.env`):

- Email: `admin@library.local`
- Password: `ChangeMe123!`

### Example requests

Register:

```bash
curl -s -X POST http://localhost:8080/api/v1/users \
  -H 'Content-Type: application/json' \
  -d '{"email":"reader@example.com","password":"ReaderPass1","fullName":"Ada Reader"}'
```

Login:

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@library.local","password":"ChangeMe123!"}' \
  | jq -r .accessToken)
```

Update a book (replace `{id}` with a seeded book id from MongoDB or Swagger):

```bash
curl -s -X PUT "http://localhost:8080/api/v1/books/{id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "title":"Effective Java",
    "authorName":"Joshua Bloch",
    "isbn":"9780134685991",
    "description":"Updated description",
    "publicationYear":2018,
    "totalCopies":5,
    "availableCopies":4
  }'
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017/library_management` | Mongo connection string |
| `SERVER_PORT` | `8080` | HTTP port |
| `JWT_SECRET` | long demo secret | HMAC signing secret (min 32 bytes; Base64 or raw UTF-8) |
| `JWT_EXPIRATION_MS` | `3600000` | Access token lifetime |
| `JWT_ISSUER` | `library-management` | JWT issuer claim |
| `SEED_ADMIN_EMAIL` | `admin@library.local` | Admin created by migration |
| `SEED_ADMIN_PASSWORD` | `ChangeMe123!` | Admin password (hashed before insert) |
| `SEED_ADMIN_FULL_NAME` | `Library Admin` | Admin display name |

Passwords are BCrypt with cost 10. JWTs are HS256 with `sub`, `email`, `roles`, `iss`, `iat`, and `exp`.

## Tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

- Unit tests cover services, validation messages, and JWT helpers (no Docker required).
- Integration tests use Testcontainers MongoDB (Docker required). They are skipped when Docker is unavailable.

Run unit tests only:

```bash
pytest tests/unit
```

## Local development without packaging the API image

```bash
docker compose up mongodb -d
python -m app
```

The process reads `SERVER_PORT` (default `8080`). A `.env` file in the working directory is loaded when present; real environment variables win.

## Patterns interns should copy

1. Keep routers thin; put business rules in services.
2. Validate input on request models and return `ApiError` for failures.
3. Map documents to responses in dedicated mapper modules.
4. Throw domain exceptions (`ConflictException`, `ResourceNotFoundException`, …) and let the handlers in `app/main.py` shape HTTP responses.
5. Protect endpoints with the JWT middleware and a role dependency, as `PUT /api/v1/books/{id}` does.
6. Add a change unit in `app/migration` for indexes and deterministic seeds.
7. Add both unit and HTTP integration tests for every new feature.
8. Document every new endpoint in the router and update the intern roadmap status.

## Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| API unhealthy on first boot | Wait for Mongo health + migrations; check `docker compose logs api` |
| `401` on book update | Login again; send `Authorization: Bearer <token>` |
| `403` on book update | Use an `ADMIN`/`LIBRARIAN` account (seeded admin works) |
| JWT secret error on startup | Set `JWT_SECRET` to at least 32 bytes |
| Integration tests fail | Ensure Docker is running for Testcontainers |

## License

Internal training material. Use and extend freely within your internship program.
