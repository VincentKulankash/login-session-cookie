--Table definitions

PRAGMA foreign_keys = ON;
--sqlite has foreign keys off by default this line turns them on (ha! ha! ha! ha!)

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lasst_login_at  TIMESTAMP,
    login_count     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS preferences (
    user_id     INTEGER PRIMARY KEY,
    theme       TEXT NOT NULL DEFAULT 'light',
    focus_mode  TEXT NOT NULL DEFAULT 'standard',
    font_size   TEXT NOT NULL DEFAULT 'medium',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS remember_tokens (
    token       TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

);


CREATE TABLE IF NOT EXISTS activity_log(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    action      TEXT NOT NULL
    detail      TEXT,
    timestamp   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

--helpful indexes for common lookups

CREATE INDEX IF NOT EXISTS idx_remember_tokens_user
    ON remember_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_activity_user_time
    ON activity_log(user_id, timestamp DESC); 


