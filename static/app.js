async function requestJSON(url, options = {}) {
    const response = await fetch(url, options);
    let data;
    try {
        data = await response.json();
    }catch {
        data = {error: `Server returned ${response.status} without valid JSON`};
    }

    if (!response.ok){
        throw new Error(data.error || `Request failed with status ${response.status}`);
    }

    return data;
}

/*Show message in the shared form in the html*/
function showMessage(text, type = 'error'){
    const box = document.getElementById('message');
    if (!box)return;
    box.textContent = text;
    box.className = `message ${type}`;

}

function clearMessage(){
    const box = document.getElementById('message');
    if(!box)return;
    box.textContent = '';
    box.className = 'message hidden';

}

function readCookie(name){
    const match = document.cookie.match(
        new RegExp('?:^|; ' + name + "=([^;]*)")
    );

    return match ? decodeURIComponent(match[1]) : null;
}


function applyPreferences(prefs= {}){
    const body = document.body;
    const theme = prefs.theme || readCookie('theme') || 'light';
    const font = prefs.font || readCookie('font_size') || 'medium';
    const focus = prefs.focus || readCookie('focus_mode') || 'standard';
    
    body.classlist.add(`theme-${theme}`);
    body.classlist.add(`font-${font}`);
    body.classlist.add(`focus-${focus}`);
}


/*Login page*/
function initLoginPage(){
    const loginView = document.getElementById('loginView');
    const signUpView = document.getElementById('signupView');

    /*Toggle between login and signup pages*/
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
    /*LOGIN submit*/
    document.getElementById('loginForm').addEventListener('submit', async (e) =>{
        e.preventDefault();
        clearMessage();
        
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const remember = document.getElementById('rememberMe').checked;

        try {
            await requestJSON('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body:JSON.stringify({username, password, remember}),
            });

        }catch (err){
            showMessage(err.message, 'error');
        }
    });

    /*SIGNUP submit*/

    document.getElementById('signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        clearMessage();

        const username = document.getElementById('signupUsername').value.trim();
        const password = document.getElementById('signupPassword').value;

        try {
            await requestJSON('/api/signup', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body:JSON.stringify({username, password}),
            });

            document.getElementById('signupUsername').value = '';
            document.getElementById('signupPassword').value = '';
            signUpView.classList.add('hidden');
            loginView.classList.remove('hidden');
            showMessage('Account created. Please login.', 'Success');

        }catch (err){
            showMessage(err.message, 'error');
        }

    });
}


/*Userpage*/

async function initUserPage(){
    applyPreferences();
    let data;

    try{
        data = await requestJSON('/api/me');
    }catch (err) {
        window.location.href = '/';
        return;
    }

    fillSessionPanel(data.session);
    fillAccountPanel(data.account);
    fillPreferencesForm(data.preferences);
    applyPreferences(data.preferences);
    fillActivityPanel(data.recent_activity);
    showCookieInspector();

    /*preferences form submit*/
    document.getElementById('preferencesForm').addEventListener('submit', async (e) =>{
        e.preventDefault()
        clearMessage(); 

        const prefs = {
            theme: document.getElementById('themeSelect').value,
            focus_mode: document.getElementById('focusSelect').value,
            font_size: document.getElementById('fontSelect').value,
        };

        try{
        const res = await requestJSON('api/preferences', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify(prefs),
        });
        applyPreferences(res.preferences || prefs);
        showMessage(err.message, 'success');

        }catch(err){
            showMessage(err.message, 'error');
        }

    });

    /*logout*/

    document.getElementById('logoutButton').addEventListener('submit', async () => {
        try{
            await requestJSON('api/logout', {method: 'POST'});
        }catch {

        }
        window,location.href = '/';
    });
}


/*small render helpers for the user page*/

function fillSessionPanel(session = {}){
    document.getElementById('sessionVisits').textContent = session.visits ?? "—";
    document.getElementById("sessionLoggedInAt").textContent =
    session.logged_in_at ?? "—";
}

function fillAccountPanel(account = {}) {
  document.getElementById("accountMemberSince").textContent =
    account.member_since ?? "—";
  document.getElementById("accountTotalLogins").textContent =
    account.total_logins ?? "—";
  document.getElementById("accountLastLogin").textContent =
    account.last_login ?? "—";
  document.getElementById("accountDevices").textContent =
    account.remembered_devices ?? "—";
}

function fillPreferencesForm(prefs = {}) {
  if (prefs.theme) document.getElementById("themeSelect").value = prefs.theme;
  if (prefs.focus_mode) document.getElementById("focusSelect").value = prefs.focus_mode;
  if (prefs.font_size) document.getElementById("fontSelect").value = prefs.font_size;
}

function fillActivityPanel(items = []) {
  const list = document.getElementById("activityList");
  if (!items.length) {
    list.innerHTML = "<li>No activity yet.</li>";
    return;
  }
  list.innerHTML = items
    .map((it) => {
      const detail = it.detail ? ` — ${it.detail}` : "";
      return `<li>${it.timestamp} · ${it.action}${detail}</li>`;
    })
    .join("");
}

/** Show which cookies JS can see (HttpOnly ones won't be here). */
function showCookieInspector() {
  const el = document.getElementById("cookieInspector");
  if (!el) return;
  el.textContent = document.cookie || "(no cookies visible to JavaScript)";
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("loginForm")) {
    initLoginPage();
  }
  if (document.getElementById("userPage")) {
    initUserPage();
  }
});