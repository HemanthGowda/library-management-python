# API Overview

Interactive docs: `/swagger-ui.html`  
OpenAPI JSON: `/v3/api-docs`

## Security

- Public: registration, login, health, Swagger
- Protected: all other routes require `Authorization: Bearer <jwt>`
- Book update additionally requires `ADMIN` or `LIBRARIAN`

JWT claims used by the middleware:

- `sub` — user id
- `email`
- `roles` — array of role names
- `iss`, `iat`, `exp`

## Error shape

All handled errors return:

```json
{
  "timestamp": "2026-01-15T10:15:30.123Z",
  "status": 400,
  "error": "Validation Failed",
  "message": "Request validation failed",
  "path": "/api/v1/users",
  "violations": [
    { "field": "email", "message": "Email must be valid" }
  ]
}
```

`violations` is omitted when the error has no field errors. Timestamps are ISO-8601 UTC. Response fields use camelCase.

## Implemented contracts

### `POST /api/v1/users`

Creates a `MEMBER` account.

- `201` with user payload (password never returned)
- `400` validation errors
- `409` duplicate email

### `POST /api/v1/auth/login`

Returns a bearer token.

- `200` with `accessToken`, `tokenType`, `expiresInMs`, `userId`, `email`, and `roles`
- `400` validation errors
- `401` invalid credentials / disabled account

### `PUT /api/v1/books/{id}`

Full update of mutable book fields.

- `200` updated book
- `400` validation / availableCopies > totalCopies
- `401` missing/invalid token
- `403` authenticated but wrong role
- `404` unknown id
- `409` ISBN belongs to another book

## Not implemented (intern backlog)

- Authors (entire resource)
- Book create/list/get/delete
- Loans
- Admin user management
