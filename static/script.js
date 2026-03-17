// ── State ─────────────────────────────────────────────────────────────────────
const API = '';  // same origin
let currentEmail = null;
let pollInterval = null;

// ── DOM Refs ──────────────────────────────────────────────────────────────────
const loginScreen    = document.getElementById('login-screen');
const dashboardScreen= document.getElementById('dashboard-screen');
const loginForm      = document.getElementById('login-form');
const emailInput     = document.getElementById('email-input');
const loginError     = document.getElementById('login-error');
const displayEmail   = document.getElementById('display-email');
const avatarInitials = document.getElementById('avatar-initials');
const statusBadge    = document.getElementById('status-badge');
const btnOn          = document.getElementById('btn-on');
const btnOff         = document.getElementById('btn-off');
const toggleMsg      = document.getElementById('toggle-msg');
const logoutBtn      = document.getElementById('logout-btn');
const activeUserDisplay = document.getElementById('active-user-display');

// ── Helpers ───────────────────────────────────────────────────────────────────
function initials(email) {
  return email ? email[0].toUpperCase() : '?';
}

function showMsg(el, text, type = '') {
  el.textContent = text;
  el.className = `toggle-msg ${type}`;
  el.classList.remove('hidden');
  clearTimeout(el._timer);
  if (type !== 'error') {
    el._timer = setTimeout(() => el.classList.add('hidden'), 5000);
  }
}

function setStatus(status) {
  if (status === 'active') {
    statusBadge.textContent = '● Active';
    statusBadge.classList.add('active-badge');
  } else {
    statusBadge.textContent = '● Inactive';
    statusBadge.classList.remove('active-badge');
  }
}

function renderActiveUser(email) {
  if (email) {
    activeUserDisplay.innerHTML = `
      <div class="active-email-row">
        <div class="active-avatar">${initials(email)}</div>
        <div class="active-email-text">${email}</div>
      </div>`;
  } else {
    activeUserDisplay.innerHTML = `
      <div class="no-active">
        <span class="no-active-icon">🔴</span>
        <p>No active user right now</p>
      </div>`;
  }
}

// ── Polling ───────────────────────────────────────────────────────────────────
async function pollActiveUser() {
  try {
    const res  = await fetch(`${API}/api/active_user`);
    const data = await res.json();
    renderActiveUser(data.email);
  } catch (_) {/* silent */}
}

function startPolling() {
  pollActiveUser();
  pollInterval = setInterval(pollActiveUser, 4000);
}

function stopPolling() {
  clearInterval(pollInterval);
  pollInterval = null;
}

// ── Screens ───────────────────────────────────────────────────────────────────
function showLogin() {
  dashboardScreen.classList.remove('active');
  loginScreen.classList.add('active');
  emailInput.value = '';
  loginError.classList.add('hidden');
  stopPolling();
}

function showDashboard(user) {
  currentEmail = user.email;
  displayEmail.textContent = user.email;
  avatarInitials.textContent = initials(user.email);
  setStatus(user.status);
  toggleMsg.classList.add('hidden');

  loginScreen.classList.remove('active');
  dashboardScreen.classList.add('active');
  startPolling();
}

// ── Login ─────────────────────────────────────────────────────────────────────
loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = emailInput.value.trim();
  if (!email) return;

  loginError.classList.add('hidden');
  try {
    const res  = await fetch(`${API}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (!res.ok) {
      const err = await res.json();
      loginError.textContent = err.detail || 'Login failed.';
      loginError.classList.remove('hidden');
      return;
    }

    const user = await res.json();
    showDashboard(user);
  } catch (err) {
    loginError.textContent = 'Could not connect to server.';
    loginError.classList.remove('hidden');
  }
});

// ── Logout ────────────────────────────────────────────────────────────────────
logoutBtn.addEventListener('click', async () => {
  // Deactivate on logout if active
  if (currentEmail) {
    try {
      await fetch(`${API}/api/deactivate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: currentEmail }),
      });
    } catch (_) {/* silent */}
  }
  currentEmail = null;
  showLogin();
});

// ── ON Button ─────────────────────────────────────────────────────────────────
btnOn.addEventListener('click', async () => {
  if (!currentEmail) return;
  try {
    const res  = await fetch(`${API}/api/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: currentEmail }),
    });
    const data = await res.json();

    if (!res.ok) {
      showMsg(toggleMsg, data.detail || 'Could not activate.', 'error');
      return;
    }
    setStatus('active');
    showMsg(toggleMsg, '✔ You are now Active!', 'success');
    pollActiveUser();
  } catch (_) {
    showMsg(toggleMsg, 'Network error. Please try again.', 'error');
  }
});

// ── OFF Button ────────────────────────────────────────────────────────────────
btnOff.addEventListener('click', async () => {
  if (!currentEmail) return;
  try {
    const res  = await fetch(`${API}/api/deactivate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: currentEmail }),
    });
    const data = await res.json();

    if (!res.ok) {
      showMsg(toggleMsg, data.detail || 'Could not deactivate.', 'error');
      return;
    }
    setStatus('inactive');
    showMsg(toggleMsg, '✖ You are now Inactive.', '');
    pollActiveUser();
  } catch (_) {
    showMsg(toggleMsg, 'Network error. Please try again.', 'error');
  }
});
