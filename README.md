# Remember-Me Cookie Demo

A small Flask app that demonstrates the difference between sessions, persistent
cookies, and account-level preferences — and where each one actually lives.

Built to learn cookies hands-on: you can see them being set in DevTools,
watch them persist across browser restarts, and observe what JS can and
can't read.

## What it does

- **Signup + login** with hashed passwords (Werkzeug).
- **"Remember me"** — generates a random token, stores it in SQLite, and
  sets a persistent HttpOnly cookie. Come back days later → auto-login.
- **Per-account preferences** (theme, focus mode, font size) that follow the
  account across devices. Stored server-side in SQLite, mirrored into
  client-readable cookies for instant rendering.
- **Session vs account data** shown side by side on the user page, plus a
  live cookie inspector.

## Setup on your machine

### Prerequisites
- Python 3.9+
- git
- No database server needed — SQLite is built into Python.

### Steps

    git clone <your-repo-url>
    cd <repo-name>

    python3 -m venv venv
    source venv/bin/activate            # Linux / macOS
    # venv\Scripts\Activate.ps1         # Windows PowerShell
    # venv\Scripts\activate.bat         # Windows cmd

    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5001/

`app.db` is created automatically on first run — no SQL needed.

Run the tests (optional):

    pytest -v

Stop the server with `Ctrl+C`. Deactivate the venv with `deactivate`.

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named 'flask'` | Activate venv, then `pip install -r requirements.txt`. |
| `No module named 'db'` | Run from the project root (where `app.py` lives). |
| `Address already in use` | Another process is on port 5001. Stop it or change the port in `app.py`. |
| `TemplateNotFound: login.html` | `templates/` folder missing or file misnamed. |
| Cookies not being set | You must visit `http://127.0.0.1:5001/`, not `file://`. |

## Project structure

    .
    ├── app.py            Flask routes, sessions, cookie handling
    ├── db.py             SQLite helpers (queries, tokens, activity log)
    ├── schema.sql        Table definitions (run at startup)
    ├── test_db.py        pytest tests for the data layer
    ├── requirements.txt  Python dependencies
    ├── app.db            Created at runtime (gitignored)
    ├── templates/
    │   ├── login.html
    │   └── user.html
    └── static/
        ├── app.js
        └── style.css

## Cookie reference

| Cookie           | Type       | HttpOnly | Lifetime      | Purpose                    |
|------------------|------------|----------|---------------|----------------------------|
| session          | Session    | Yes      | Browser close | Who is logged in           |
| remember_token   | Persistent | Yes      | 30 days       | Auto-login across sessions |
| theme            | Persistent | No       | 1 year        | UI preference (mirror)     |
| focus_mode       | Persistent | No       | 1 year        | UI preference (mirror)     |
| font_size        | Persistent | No       | 1 year        | UI preference (mirror)     |

## DevTools test

1. Log in with **Remember me** checked.
2. DevTools → Application → Cookies — five cookies appear.
3. Console → `document.cookie` — you see the three preference cookies, **not**
   `session` or `remember_token` (they're HttpOnly).
4. Close the browser, reopen, visit `/` → auto-redirected to `/user`.
5. Log out — session and remember-token cookies cleared; preference cookies
   remain (they're device preferences, not auth).
6. Open an incognito window, log in as the same user → preferences follow
   the account, not the browser.

## What I learned

- **Session cookies vs persistent cookies** — lifetime is separate from where
  the data lives. "Session" means "dies when the browser closes." "Persistent"
  means "survives until expiry." Both live in the browser.
- **Where session data actually lives** — Flask's default session stores the
  data *inside* the signed cookie, not on the server. It's signed (tamper-proof)
  but not encrypted (readable).
- **Why "remember me" needs a token** — you can't safely store a password in a
  cookie, so you store a random token that the server looks up in a DB. Delete
  the row → the device is forgotten.
- **Why HttpOnly matters** — JavaScript can't read `session` or
  `remember_token`, so an XSS attack can't steal the login. Preference cookies
  are readable on purpose, so the UI can apply them before `/api/me` returns.
- **Account vs device preferences** — account preferences (theme) live
  server-side so they follow the user across devices. Device preferences would
  live in client cookies only.
- **Why GET must be safe** — GET should never modify data; otherwise browsers,
  crawlers, or prefetchers could accidentally change things. Modifying data
  belongs in POST, PUT, PATCH, or DELETE.
- **RESTful route naming** — plural nouns (`/api/events`), HTTP methods carry
  the action, status codes tell the story (201 for create, 400 for bad input,
  404 for missing, 204 for empty success).

## Known limitations

- SQLite is local; not designed for multi-instance deployment.
- `SECRET_KEY` in `app.py` is a class-demo value — replace it in production.
- Cookies aren't marked `Secure` because this runs over HTTP locally.
- The free-tier deployment story (e.g. Render) resets `app.db` on redeploy —
  fine for a demo, not for real data.