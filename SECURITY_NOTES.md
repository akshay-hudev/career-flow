# Security Notes — Known Issues (Deferred)

**Status as of 2026-08-15:** The application runs locally and all 48 backend tests
pass. The issues below are **known and deliberately deferred** — they are *not*
blocking local development, but the API **must not be exposed publicly** until the
HIGH/BLOCKER items are fixed.

Each item lists severity, location, impact, and a recommended fix so this can be
picked up later without re-auditing.

---

## 1. Broken object-level authorization (IDOR) — 🔴 BLOCKER

Most data routes accept a **client-supplied `user_id`** (or a bare resource id)
and perform **no ownership check** against an authenticated user. Several have no
authentication at all. Any client can read, modify, or delete *any* user's data
by iterating integer IDs.

| Route | Location | Problem |
|-------|----------|---------|
| `GET /api/v1/resume/{user_id}/list` | `backend/routers/resume.py:65` | Unauthenticated; lists any user's resumes |
| `GET /api/v1/resume/{resume_id}` | `backend/routers/resume.py:72` | Unauthenticated; reads any resume |
| `DELETE /api/v1/resume/{resume_id}` | `backend/routers/resume.py:81` | Unauthenticated; deletes any resume |
| `POST /api/v1/match/score` | `backend/routers/match.py:16` | Unauthenticated; scores any `resume_id` |
| `POST /api/v1/match/advice` | `backend/routers/match.py:41` | Unauthenticated; runs advice (incl. paid Gemini calls) on any `resume_id` |
| `POST /api/v1/jobs/save?user_id=` | `backend/routers/jobs.py:45` | `user_id` from query; save to any user's board |
| `GET /api/v1/jobs/saved/{user_id}` | `backend/routers/jobs.py:83` | Unauthenticated; read any user's saved jobs |
| `PATCH /api/v1/jobs/saved/{job_id}/status` | `backend/routers/jobs.py:96` | Unauthenticated; mutate any saved job |
| `DELETE /api/v1/jobs/saved/{job_id}` | `backend/routers/jobs.py:119` | Unauthenticated; delete any saved job |

**Note:** `POST /api/v1/resume/upload` is already protected — it uses
`Depends(get_current_user)` and derives the owner from the JWT (`current_user.id`),
ignoring any client-supplied `user_id`. Use it as the template for the others.

**Recommended fix**
- Add `current_user: User = Depends(get_current_user)` to every route above.
- Derive `user_id` from `current_user.id` — never from the request body/query/path.
- For resource-id routes (`resume_id`, `job_id`), fetch the row then verify
  `row.user_id == current_user.id`; return `404` (not `403`) on mismatch to avoid
  leaking existence.
- Drop the now-redundant `user_id` path/query params, changing the contract to
  `GET /resume/list` and `GET /jobs/saved`. Update the frontend calls in
  `frontend/src/api/client.js` accordingly.
- In `backend/tests/conftest.py`, make the `override_get_current_user` user the
  **same** user the `test_user` fixture creates, so ownership checks pass and the
  suite stays green.

---

## 2. Unauthenticated user creation + enumeration — 🟠 HIGH

- `POST /api/v1/users/` (`backend/routers/users.py:10`) creates a user with **no
  password**, and returns the existing record for a known email. This sidesteps
  the real `/auth/register` flow and enables account pre-creation.
- `GET /api/v1/users/{user_id}` (`backend/routers/users.py:22`) is unauthenticated
  and returns email + name for any integer id → **user enumeration / PII leak**.

**Recommended fix:** Remove `POST /users/` (superseded by `/auth/register`), or
restrict it to an admin context. Protect `GET /users/{id}` with
`get_current_user` and allow self-only, or drop it in favor of `/auth/me`.

---

## 3. Default `SECRET_KEY` allows JWT forgery — 🟠 HIGH

`backend/config.py:19` defaults `SECRET_KEY = "change-this-in-production"`, and
`.env.example:18` ships a placeholder. If deployed without overriding it, JWTs are
signed with a **publicly known key** — anyone can forge a valid token for any
user id. Combined with #1, this is full account takeover.

**Recommended fix:** Fail fast at startup — raise if `SECRET_KEY` is the default/
placeholder while `DEBUG` is `False`. Document generating a strong key, e.g.
`python -c "import secrets; print(secrets.token_urlsafe(48))"`.

---

## 4. CORS allows all origins, ignores config — 🟡 MEDIUM

`backend/main.py:26` hardcodes `allow_origins=["*"]` and ignores
`settings.CORS_ORIGINS`. `allow_credentials=False` means this is not an immediate
cookie-theft vector (auth is via the `Authorization` header), but any site can
call the API, and the configured allow-list is dead.

**Recommended fix:** Read `settings.CORS_ORIGINS`; restrict to the known frontend
origin(s) in production.

---

## 5. Frontend never validates the stored token — 🟡 MEDIUM

`frontend/src/api/client.js` stores `career_token`/`career_user` in localStorage
and attaches the token, but never verifies it on load. A stale/tampered token is
only discovered on the first `401` (the interceptor then clears storage and
redirects to `/login`). Not a server vulnerability, but weak session integrity.

**Recommended fix:** Call `GET /auth/me` on app boot; clear the session and
redirect if it fails.

---

## 6. Password hashing hardening — 🟢 LOW (mostly resolved 2026-08-16)

**Resolved:** `passlib` (unmaintained, and the direct cause of a hard `500` on
`/auth/register` under `bcrypt` 5.x) has been removed. `backend/services/auth_service.py`
now calls `bcrypt` directly, the dependency is pinned to `bcrypt>=4.0.1`, and
passwords are truncated to 72 bytes explicitly so long inputs no longer raise.

**Remaining (cosmetic):** the `password` field in `backend/schemas/schemas.py`
still has no `max_length`, so a password over 72 bytes is silently truncated to
72 rather than rejected. Add `max_length=72` (or a validator) to reject them
explicitly if desired.

---

## 7. Redundant `user_id` on resume upload — ⚪ INFO

`frontend/src/api/client.js:45` still sends `?user_id=` to
`POST /resume/upload`, but the backend now derives the owner from the JWT and
ignores it (`backend/routers/resume.py:23`). Harmless, but misleading — remove
once #1 is addressed.

---

### Fixing later

Items #1–#3 are the ones that gate a public deploy. #1 and the frontend token
work (#5) touch both backend and frontend; #2–#4, #6 are backend-only. When you're
ready, a single "security hardening" pass can land #1–#4 and #6 together and keep
the test suite green with the conftest change noted in #1.
