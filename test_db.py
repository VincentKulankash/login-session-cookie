import os
import pytest
from datetime import datetime, timedelta

import db

@pytest.fixture(autouse=True)
def fresh_db():

    """
    Before each test:
      - delete app.db (if it exists)
      - recreate it from schema.sql
    Gives every test a clean, known state.
    """
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)

    db.init_db()
    yield

"""Users"""
def test_create_and_fetch_users():
    uid = db.create_user('alice', 'hash1')
    assert isinstance(uid, int)

    user = db.get_user_by_username('alice')
    assert user is not None
    assert user ['username'] == 'alice'
    assert user ['password_hash'] == 'hash1'
    assert user ['login_count'] == 0
    assert user ['last_login_at'] is None


def test_get_user_by_id():
    uid = db.create_user('bob', 'hash2')
    user = db.get_user_by_id(uid)
    assert user ['username'] == 'bob'

def test_get_missing_user_returns_none():
    assert db.get_user_by_username('nobody') is None
    assert db.get_user_by_id(9999) is None

def test_touch_login_increments():
    uid = db.create_user('carol', 'hash3')
    db.touch_login(uid)
    db.touch_login(uid)

    user = db.get_user_by_id(uid)
    assert user ['login_count'] == 2
    assert user ['last_login_at'] is not None

"""Preferences"""

def test_preferences_defaults_when_missing():
    uid = db.create_user("dave", "hash4")
    prefs = db.get_preferences(uid)
    assert prefs == {"theme": "light", "focus_mode": "standard", "font_size": "medium"}


def test_save_preferences_inserts_then_updates():
    uid = db.create_user("erin", "hash5")

    db.save_preferences(uid, "dark", "deep", "large")
    prefs = db.get_preferences(uid)
    assert prefs == {"theme": "dark", "focus_mode": "deep", "font_size": "large"}

    # Upsert a second time — should update, not duplicate
    db.save_preferences(uid, "light", "revision", "small")
    prefs = db.get_preferences(uid)
    assert prefs == {"theme": "light", "focus_mode": "revision", "font_size": "small"}


"""Remember tokens"""
def test_remember_token_valid():
    uid = db.create_user("frank", "hash6")
    future = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    db.create_remember_token("tok-abc", uid, future)

    user = db.find_user_by_token("tok-abc")
    assert user is not None
    assert user["username"] == "frank"
    assert "expires_at" not in user


def test_remember_token_expired_is_deleted():
    uid = db.create_user("gina", "hash7")
    past = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    db.create_remember_token("tok-old", uid, past)

    user = db.find_user_by_token("tok-old")
    assert user is None
    assert db.count_token_for_user(uid) == 0


def test_remember_token_unknown_returns_none():
    assert db.find_user_by_token("does-not-exist") is None


def test_delete_token():
    uid = db.create_user("hank", "hash8")
    future = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    db.create_remember_token("tok-h", uid, future)

    assert db.count_token_for_user(uid) == 1
    db.delete_token("tok-h")
    assert db.count_token_for_user(uid) == 0


def test_delete_all_tokens_for_user():
    uid = db.create_user("ivy", "hash9")
    future = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    db.create_remember_token("tok-1", uid, future)
    db.create_remember_token("tok-2", uid, future)
    assert db.count_token_for_user(uid) == 2

    db.delete_all_tokens_for_user(uid)
    assert db.count_token_for_user(uid) == 0


# ---------------- Activity log ----------------

def test_log_and_get_recent_activity():
    uid = db.create_user("jake", "hash10")
    db.log_activity(uid, "signup")
    db.log_activity(uid, "login")
    db.log_activity(uid, "preference_change", "theme=dark")

    activity = db.get_recent_activity(uid)
    assert activity[0]["action"] == "preference_change"
    assert activity[0]["detail"] == "theme=dark"
    # Sanity: the oldest is at the end
    assert activity[2]["action"] == "signup"


def test_activity_respects_limit():
    uid = db.create_user("kim", "hash11")
    for i in range(5):
        db.log_activity(uid, f"event{i}")

    activity = db.get_recent_activity(uid, limit=3)
    assert len(activity) == 3