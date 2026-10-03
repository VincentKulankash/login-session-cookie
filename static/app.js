/* Shared helpers */

async function requestJSON(url, options = {}) {
    const response = await fetch(url, options);
    let data;

    try {
        data = await response.json();
    } catch {
        data = { error: `Server returned ${response.status} without valid JSON` };
    }

    if (!response.ok) {
        throw new Error(data.error || `Request failed with status ${response.status}`);
    }

    return data;
}

/* Show message in the shared form in the html */
function showMessage(text, type = 'error') {
    const box = document.getElementById('message');
    if (!box) return;
    box.textContent = text;
    box.className = `message ${type}`;
}

function clearMessage() {
    const box = document.getElementById('message');
    if (!box) return;
    box.textContent = '';
    box.className = 'message hidden';
}

/* Read a cookie value by name from document.cookie */
function readCookie(name) {
    const match = document.cookie.match(
        new RegExp('(?:^|; )' + name + '=([^;]*)')
    );
    return match ? decodeURIComponent(match[1]) : null;
}

/* Apply theme, font size and focus mode as CSS classes on <body>.
   Strips any existing preference classes first so switching works */
function applyPreferences(prefs = {}) {
    const body = document.body;
    const theme = prefs.theme      || readCookie('theme')      || 'light';
    const font  = prefs.font_size  || readCookie('font_size')  || 'medium';
    const focus = prefs.focus_mode || readCookie('focus_mode') || 'standard';

    /* Remove existing preference classes so old ones don't linger */
    body.className = body.className
        .split(' ')
        .filter(c => !/^(theme|font|focus)-/.test(c))
        .join(' ');

    body.classList.add(`theme-${theme}`);
    body.classList.add(`font-${font}`);
    body.classList.add(`focus-${focus}`);
}


/* Login page */

function initLoginPage() {
    const loginView = document.getElementById('loginView');
    const signUpView = document.getElementById('signupView');

    /* Toggle between login and signup views */
    document.getElementById('showSignup').addEventListener('click', (e) => {
        e.preventDefault();
        clearMessage();
        loginView.classList.add('hidden');
        signUpView.classList.remove('hidden');
    });

    document.getElementById('showLogin').addEventListener('click', (e) => {
        e.preventDefault();
        clearMessage();
        signUpView.classList.add('hidden');
        loginView.classList.remove('hidden');
    });

    /* LOGIN submit */
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearMessage();

        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const remember = document.getElementById('rememberMe').checked;

        try {
            await requestJSON('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, remember }),
            });

            /* Success: real navigation to the user page */
            window.location.href = '/user';
        } catch (err) {
            showMessage(err.message, 'error');
        }
    });

    /* SIGNUP submit */
    document.getElementById('signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearMessage();

        const username = document.getElementById('signupUsername').value.trim();
        const password = document.getElementById('signupPassword').value;

        try {
            await requestJSON('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            document.getElementById('signupUsername').value = '';
            document.getElementById('signupPassword').value = '';
            signUpView.classList.add('hidden');
            loginView.classList.remove('hidden');
            showMessage('Account created. Please log in.', 'success');
        } catch (err) {
            showMessage(err.message, 'error');
        }
    });
}


/* User page */

async function initUserPage() {
    /* Apply preferences from cookies immediately so the page
       doesn't flash the wrong theme while /api/me is loading */
    applyPreferences();

    let data;
    try {
        data = await requestJSON('/api/me');
    } catch {
        window.location.href = '/';
        return;
    }

    fillSessionPanel(data.session);
    fillAccountPanel(data.account);
    fillPreferencesForm(data.preferences);
    applyPreferences(data.preferences);
    fillActivityPanel(data.recent_activity);
    showCookieInspector();

    /* Preferences form submit */
    document.getElementById('preferencesForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearMessage();

        const prefs = {
            theme: document.getElementById('themeSelect').value,
            focus_mode: document.getElementById('focusSelect').value,
            font_size: document.getElementById('fontSelect').value,
        };

        try {
            const res = await requestJSON('/api/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(prefs),
            });
            applyPreferences(res.preferences || prefs);
            showMessage('Preferences saved.', 'success');
        } catch (err) {
            showMessage(err.message, 'error');
        }
    });

    /* Logout button — click event, not submit */
    document.getElementById('logoutButton').addEventListener('click', async () => {
        try {
            await requestJSON('/api/logout', { method: 'POST' });
        } catch {
            /* ignore — we're leaving anyway */
        }
        window.location.href = '/';
    });
}


/* Small render helpers for the user page */

function fillSessionPanel(session = {}) {
    document.getElementById('sessionVisits').textContent = session.visits ?? '—';
    document.getElementById('sessionLoggedInAt').textContent =
        session.logged_in_at ?? '—';
}

function fillAccountPanel(account = {}) {
    document.getElementById('accountMemberSince').textContent =
        account.member_since ?? '—';
    document.getElementById('accountTotalLogins').textContent =
        account.total_logins ?? '—';
    document.getElementById('accountLastLogin').textContent =
        account.last_login ?? '—';
    document.getElementById('accountDevices').textContent =
        account.remembered_devices ?? '—';
}

function fillPreferencesForm(prefs = {}) {
    if (prefs.theme)      document.getElementById('themeSelect').value = prefs.theme;
    if (prefs.focus_mode) document.getElementById('focusSelect').value = prefs.focus_mode;
    if (prefs.font_size)  document.getElementById('fontSelect').value  = prefs.font_size;
}

function fillActivityPanel(items = []) {
    const list = document.getElementById('activityList');
    if (!items.length) {
        list.innerHTML = '<li>No activity yet.</li>';
        return;
    }
    list.innerHTML = items
        .map((it) => {
            const detail = it.detail ? ` — ${it.detail}` : '';
            return `<li>${it.timestamp} · ${it.action}${detail}</li>`;
        })
        .join('');
}

/* Show which cookies JS can see (HttpOnly ones won't be here) */
function showCookieInspector() {
    const el = document.getElementById('cookieInspector');
    if (!el) return;
    el.textContent = document.cookie || '(no cookies visible to JavaScript)';
}


/* Boot: detect which page loaded and wire up the right handlers */

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('loginForm')) {
        initLoginPage();
    }
    if (document.getElementById('userPage')) {
        initUserPage();
    }
});