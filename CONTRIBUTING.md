# Contributing

This repository is a teaching codebase. Prefer clarity and consistency with the existing slices over clever abstractions.

## Before you start

1. Read [README.md](README.md) for architecture and run instructions.
2. Read [docs/intern-roadmap.md](docs/intern-roadmap.md) and pick the next incomplete milestone.
3. Skim the reference implementations:
   - User registration: `app/user`
   - Book update: `app/book`
   - Auth/JWT: `app/auth`
   - Errors: `app/exception` + `app/api/errors.py`
   - Migrations: `app/migration`

## Branching

- Create a feature branch from `main`: `feature/<short-description>`
- Keep PRs focused on one milestone when possible

## Implementation checklist

For every new API:

- [ ] Document/model + repository
- [ ] Request/response models with validation
- [ ] Service with clear business rules
- [ ] Router with OpenAPI summary, description, and responses
- [ ] Role checks when needed (see `require_catalog_manager`)
- [ ] Change unit for indexes/seeds if the schema changes
- [ ] Unit tests for service rules
- [ ] Integration test covering happy path + auth/validation failures
- [ ] README / roadmap updates if the milestone status changes

## Coding conventions

- Python 3.12, FastAPI, Pydantic v2
- Package by feature (`author`, `loan`, …), not by technical layer alone
- Do not put business logic in routers or repositories
- Never commit secrets; use `.env` / environment variables
- Do not log passwords or raw JWTs

## Tests

```bash
pytest
```

Docker must be available for Testcontainers-based integration tests.

## Documentation

- Update router summaries and response declarations
- Keep error responses aligned with `ApiError`
- Mark completed roadmap items as done in `docs/intern-roadmap.md`

## Review expectations

Reviewers will look for:

1. Pattern parity with the existing slices
2. Validation and authorization coverage
3. Tests that would catch regressions
4. Clear migration strategy for Mongo collections/indexes
