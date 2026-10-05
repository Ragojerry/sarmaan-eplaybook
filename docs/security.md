# Security & Authentication — Phase 4

## 1. Endpoints (exactly per master prompt §52)

| Endpoint | Behavior |
|---|---|
| `POST /auth/login` | Username + password → access token (30 min) + refresh token (30 days). Deliberately identical error message for "no such user" and "wrong password" — distinguishing them would let an attacker enumerate valid usernames. Checks `status == ACTIVE` — suspended/inactive accounts are rejected even with a correct password. Writes `last_login_at` and an `audit_logs` LOGIN entry. |
| `POST /auth/refresh` | Refresh token → new access token. Validates the token is of type `refresh`, still stored, **not revoked**, and not expired. |
| `POST /auth/logout` | Requires a valid access token (who's logging out) + the refresh token to revoke. Sets `refresh_tokens.revoked = true` — a genuinely revoked token, not a client-side "forget it and hope" no-op. Writes an audit_logs LOGOUT entry. |
| `GET /auth/me` | Requires a valid access token. Returns the current user's profile. |

## 2. Password storage

Argon2 via `passlib` (`app/auth/security.py`) — never plaintext, never a fast general-purpose hash like plain SHA-256. Matches master prompt's "do not store passwords locally in plain text" (§51) and "use secure password hashing" (§52).

## 3. Tokens

- **Access tokens**: JWT (HS256), 30 min expiry, carries `sub` (user id), `role`, `type: "access"`. Short-lived by design — if leaked, the exposure window is small.
- **Refresh tokens**: JWT, 30 day expiry, carries `sub`, `type: "refresh"`. Also stored in the `refresh_tokens` table so it can be **revoked server-side** on logout — an unstored JWT can't be invalidated before its natural expiry, which would make logout meaningless for a stolen token.
- `jwt_secret_key` (`backend/.env`) **must** be a real random secret in any shared/staging/production environment — the checked-in `.env.example` value is a placeholder, not a secret.

## 4. RBAC

`app/auth/dependencies.py`:
- `get_current_user` — decodes and validates the access token, re-loads the user from the DB (so a suspended account is locked out immediately, not just at its next login/token-refresh), and rejects anything not `status == ACTIVE`.
- `require_roles(*allowed)` — dependency factory. `SUPER_ADMIN` always passes regardless of the allowed list (the one role every governance/admin action must permit); anyone else must have one of the explicitly listed roles or gets a 403.

The 8 roles (`RoleName` enum, `app/models/enums.py`) match master prompt §"roles" exactly: `SUPER_ADMIN`, `CONTENT_ADMIN`, `PROGRAM_REVIEWER`, `LOCALISATION_REVIEWER`, `TECHNICAL_REVIEWER`, `SUPERVISOR`, `CDD`, `READ_ONLY`.

**Only one endpoint currently demonstrates RBAC in practice**: `POST /modules` requires `CONTENT_ADMIN` (or `SUPER_ADMIN`) — this exists specifically to prove the mechanism works end-to-end (verified by `tests/test_auth.py::test_rbac_blocks_non_admin_role`, which logs in as a `CDD` user and confirms a 403). Applying `require_roles(...)` to the rest of the real endpoints (content, releases, users, etc.) happens as those endpoints are built out in Phase 5/6 — the mechanism is proven now so later phases just apply it, not re-invent it.

## 5. Verified (not just written)

`backend/tests/test_auth.py` — 6 automated tests, run against a real PostgreSQL instance (not mocked), confirmed passing twice in a row against the same database to check for state leakage between runs:

1. Wrong password → 401
2. Correct login → returns both tokens
3. `/auth/me` with no token → 401
4. `/auth/me` with valid token → returns the correct user
5. `POST /modules` as a `CDD` user → 403 (RBAC actually blocks, not just decorates)
6. Refresh → succeeds; logout → 204; **reusing the same refresh token after logout → 401** (proves revocation is real, not cosmetic)

Run it yourself:
```bash
cd backend
python3 -m alembic upgrade head   # if not already migrated
python3 -m pytest tests/test_auth.py -v
```

## 6. Known gaps / next steps

- No rate-limiting on `/auth/login` yet (brute-force protection) — worth adding before any public-facing deployment.
- No password-reset flow yet — not in the master prompt's §52 endpoint list, so deliberately out of Phase 4's scope; flag if it's needed.
- `require_roles` is only applied to one demo endpoint so far, as noted in §4 — real coverage grows with Phase 5/6 endpoints.
- Refresh token rotation (issuing a new refresh token on every `/auth/refresh` call, invalidating the old one) is not implemented — currently a single refresh token remains valid for its full 30-day life unless explicitly logged out. Worth a decision on whether rotation is required before production use.
