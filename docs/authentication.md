# Authentication

## Overview

Single sign-in system for all roles (ADMIN_HR, EMPLOYER, EMPLOYEE). No separate logins per role.

- **Access tokens**: short-lived signed JWTs (default 30 min), stateless.
- **Refresh tokens**: opaque random strings stored hashed in `refresh_tokens`, individually revocable, rotated on every use (default 7 days).

## Password storage

Argon2id via `argon2-cffi` (OWASP-recommended, memory-hard). All hashing/verification is centralized in `app/core/security.py`:

- `hash_password(password)`
- `verify_password(password, password_hash)`

Never store or log plain-text passwords. `verify_password` returns `False` for malformed hashes rather than raising.

## Token lifecycle

### Login

`POST /api/v1/auth/login` — OAuth2 password flow (`username` = email, `password`).

1. Verify credentials (Argon2id check).
2. Reject inactive accounts (403).
3. Update `last_login_at`.
4. Return `{access_token, refresh_token, token_type: "bearer"}`.

### Access token

JWT payload contains only non-sensitive identity claims:

```
sub, user_id, role, company_id, token_type="access", iat, exp
```

Decoded/validated in `get_current_user` (`app/dependencies/auth.py`). Every protected endpoint resolves the user through this dependency.

### Refresh token

- Generated with `secrets.token_urlsafe(48)`; only its SHA-256 hash is stored.
- `POST /api/v1/auth/refresh` validates it (not revoked, not expired), revokes it, and issues a fresh access + refresh token pair (rotation). Replaying a rotated token fails with 401.
- `POST /api/v1/auth/logout` revokes the presented refresh token.

Why DB-backed refresh tokens instead of JWTs: it gives real revocation (logout, compromise), rotation detection, and per-device control. The access token stays stateless so `GET /auth/me` etc. require no DB write.

## Registration

`POST /api/v1/auth/register` — **Admin/HR only** (requires `user.create` permission). Users are created inside the calling admin's company; a non-admin gets 403. This keeps the system closed and tenant-scoped — there is no open public signup.

## Error semantics

| Case | Status |
| --- | --- |
| Bad credentials / bad token / bad refresh token | 401 |
| Inactive account at login / expired permissions | 403 |
| Duplicate email | 409 |
| Unknown role, short password | 422 |

## Security notes

- `SECRET_KEY` comes from the environment (`.env`), never source control.
- Argon2 hashes are computationally expensive by design; login is rate-limitable later without changes.
- JWT carries no sensitive data beyond identity scoping.
- Refresh token hashing means a DB leak does not leak usable refresh tokens.
