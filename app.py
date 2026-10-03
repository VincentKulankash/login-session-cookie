#In charge of flask routes, session logic, cookie handling
from flask import (
    Flask,
    session,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    make_response
)

from werkzeug.security import generate_password_hash, check_password_hash

import db 
import os 
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-for-class-demo'

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

REMEMBER_DAYS = 30
REMEMBER_SECONDS = REMEMBER_DAYS * 24 * 60 * 60

db.init_db()

def current_user_id():
    return session.get("user_id")

def utc_iso(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def set_preference_cookies(response, prefs):
    one_year = 365 * 24 * 60 * 60
    response.set_cookie('theme', prefs['theme'], max_age=one_year) 
    response.set_cookie('focus_mode', prefs['focus_mode'], max_age=one_year) 
    response.set_cookie("font_size",  prefs["font_size"],  max_age=one_year)

def clear_preference_cookie(response):
    for name in ('theme', 'focus_mode', 'font_size'):
        response.delete_cookie(name)

def set_remember_cookie(response, token):
    response.set_cookie(
        'remember_token',
        token,
        max_age=REMEMBER_SECONDS,
        httponly=True,
        samesite='Lax',
    )

def clear_remember_cookie(response):
    response.delete_cookie('remember_token')

@app.before_request
def auto_login_from_remember_token():
    """Runs before every request. if the user isn't logged in (no session) but has a valid remember me token cookie rebuild the session from it"""

    if session.get('user_id'):
        return 
    if request.endpoint in ('login', 'signup'):
        return #don't suto login when the user is trying to login/signup endpoints 

    token = request.cookies.get('remember_token')
    if not token:
        return
    user = db.find_user_by_token(token)
    if not user:
        return

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['logged_in_at'] = datetime.utcnow().isoformat(timespec='seconds')
    db.log_activity(user['id'], 'auto_login')


#Page routes 

@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('user_page'))
    return render_template('login.html')

@app.route('/user')
def user_page():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    return render_template('user.html', username=session.get('username'))

#API SIGNUP

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error':'Username and password are required'}), 400

    if db.get_user_by_username(username):
        return jsonify({'error':'That username is already taken'}), 400

    password_hash = generate_password_hash(password)
    user_id = db.create_user(username, password_hash)

    db.save_preferences(user_id, 'light', 'standard', 'medium')
    db.log_activity(user_id, 'signup')

    return jsonify({'message':'Account created.','username': username}), 201

#API LOGIN 
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    remember = bool(data.get('remember'))

    user = db.get_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify ({'error':'Invalid username or paswword.'}), 401

    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['logged_in_at'] = datetime.utcnow().isoformat(timespec='seconds')

    db.touch_login(user['id'])
    db.log_activity(user['id'], 'login')

    response = make_response(jsonify({
        'message': 'Login successful',
        'username': user['username'],
    }))
    #Mirror preferences into client cookies
    prefs = db.get_preferences(user['id'])
    set_preference_cookies(response, prefs)

    if remember:
        token = secrets.token_urlsafe(32)
        expires_at = utc_iso(datetime.utcnow() + timedelta(days=REMEMBER_DAYS))
        db.create_remember_token(token, user['id'], expires_at)
        set_remember_cookie(response, token)

    return response
@app.route('/api/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    token = request.cookies.get('remember_token')

    if token:
        db.delete_token(token)

    if user_id:
        db.log_activity(user_id, 'logout')

    session.clear()

    response = make_response(jsonify({'message': 'Logged Out.'}))
    clear_remember_cookie(response)

    return response


@app.route('/api/me')
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authorized'}), 401

    session['visits'] = session.get('visits', 0) + 1

    user = db.get_user_by_id(user_id)
    prefs = db.get_preferences(user_id)
    activity = db.get_recent_activity(user_id, limit=10)
    devices = db.count_token_for_user(user_id)

    return jsonify({
        'username': user['username'],
        'session': {
            'visits': session['visits'],
            'logged_in_at': session.get('logged_in_at'),
        },
        'account': {
            'member_since': user['created_at'],
            'total_logins': user['login_count'],
            'last_login': user['last_login_at'],
            'remembered_devices': devices,
        },
        'preferences': prefs,
        'recent_activity': activity,
    }), 200

#api preferences
ALLOWED_THEMES = {'light', 'dark'}
ALLOWED_FOCUS = {'standard', 'deep', 'revision', 'practice'}
ALLOWED_FONTS = {'small', 'medium', 'large'}

@app.route('/api/preferences', methods=['POST'])
def update_preferences():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.get_json(silent=True) or {}
    theme = data.get('theme', 'light')
    focus_mode = data.get('focus_mode', 'standard')
    font_size = data.get('font_size', 'medium')

    if theme not in ALLOWED_THEMES:
        return jsonify({'error': 'Invalid theme.'}), 400
    if focus_mode not in ALLOWED_FOCUS:
        return jsonify({'error': 'Invalid focus mode.'}), 400
    if font_size not in ALLOWED_FONTS:
        return jsonify({'error': 'Invalid font size.'}), 400

    db.save_preferences(user_id, theme, focus_mode, font_size)
    db.log_activity(user_id, 'preference change', f"theme={theme}")

    response = make_response(jsonify({
        'message': 'Preference saved',
        'preferences': {
            'theme': theme,
            'focus_mode': focus_mode,
            "font_size": font_size,
        },
    }))

    set_preference_cookies(response, {
        'theme': theme, 'focus_mode': focus_mode, 'font_size': font_size,
    })

    return response




if __name__ == '__main__':
    app.run(debug=True, port=5001)
    
     