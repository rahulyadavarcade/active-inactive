const API = '';

const userListBody = document.getElementById('user-list-body');
const addUserForm = document.getElementById('add-user-form');
const formMsg = document.getElementById('form-msg');

function showMsg(text, type = '') {
    formMsg.textContent = text;
    formMsg.className = `toggle-msg ${type}`;
    formMsg.classList.remove('hidden');
    setTimeout(() => formMsg.classList.add('hidden'), 5000);
}

async function loadUsers() {
    const savedUser = JSON.parse(localStorage.getItem('toilet_user') || '{}');
    const adminEmail = savedUser.email || '';

    try {
        const res = await fetch(`${API}/api/users`, {
            headers: { 'admin-email': adminEmail }
        });

        if (res.status === 403) {
            alert("Access Denied: You are not an admin.");
            window.location.href = '/';
            return;
        }

        const users = await res.json();

        userListBody.innerHTML = users.map(user => `
      <tr>
        <td style="font-weight: 600;">${user.username}</td>
        <td style="color: var(--muted);">${user.email}</td>
        <td>
          <span class="status-badge ${user.status === 'active' ? 'active-badge' : ''}">
            ${user.status}
          </span>
        </td>
        <td>
          <button class="delete-btn" onclick="deleteUser('${user.email}')">Delete</button>
        </td>
      </tr>
    `).join('');
    } catch (err) {
        console.error('Failed to load users', err);
    }
}

async function deleteUser(email) {
    if (!confirm(`Are you sure you want to delete ${email}?`)) return;

    const savedUser = JSON.parse(localStorage.getItem('toilet_user') || '{}');
    const adminEmail = savedUser.email || '';

    try {
        const res = await fetch(`${API}/api/users/${email}`, {
            method: 'DELETE',
            headers: { 'admin-email': adminEmail }
        });
        const data = await res.json();

        if (res.ok) {
            showMsg('User deleted successfully', 'success');
            loadUsers();
        } else {
            showMsg(data.detail || 'Delete failed', 'error');
        }
    } catch (err) {
        showMsg('Network error', 'error');
    }
}

addUserForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('new-email').value.trim();
    const username = document.getElementById('new-username').value.trim();

    const savedUser = JSON.parse(localStorage.getItem('toilet_user') || '{}');
    const adminEmail = savedUser.email || '';

    try {
        const res = await fetch(`${API}/api/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'admin-email': adminEmail
            },
            body: JSON.stringify({ email, username })
        });
        const data = await res.json();

        if (res.ok) {
            showMsg('User added successfully', 'success');
            addUserForm.reset();
            loadUsers();
        } else {
            showMsg(data.detail || 'Failed to add user', 'error');
        }
    } catch (err) {
        showMsg('Network error', 'error');
    }
});

// Initial load
loadUsers();
