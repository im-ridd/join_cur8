// Empty string = same-origin (admin panel served by the backend itself)
const API = '';

function showLoginOverlay() {
  document.getElementById('login-overlay').classList.add('active');
}
function hideLoginOverlay() {
  document.getElementById('login-overlay').classList.remove('active');
  document.getElementById('login-err').textContent = '';
}

async function apiFetch(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' }, credentials: 'include' };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (res.status === 401) { showLoginOverlay(); return null; }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = Array.isArray(data.detail) ? (data.detail[0]?.msg || res.statusText) : (data.detail || res.statusText);
    throw new Error(msg);
  }
  return data;
}

// -- Login --------------------------------------------------------------------
document.getElementById('btn-do-login').addEventListener('click', async () => {
  const username = document.getElementById('login-user').value.trim();
  const password = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-err');
  errEl.textContent = '';
  try {
    const res = await fetch(API + '/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    hideLoginOverlay();
    loadDashboard();
  } catch (e) {
    errEl.textContent = e.message;
  }
});
document.getElementById('login-pass').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('btn-do-login').click();
});

// -- Navigation ---------------------------------------------------------------
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const page = link.dataset.page;
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    link.classList.add('active');
    document.getElementById('page-' + page).classList.add('active');
    if (page === 'dashboard') loadDashboard();
    if (page === 'users') loadUsers();
    if (page === 'referrer-settings') loadReferrerConfigs();
    if (page === 'delegations') loadDelegations();
  });
});

// -- Logout -------------------------------------------------------------------
document.getElementById('btn-logout').addEventListener('click', async () => {
  await fetch(API + '/admin/logout', { method: 'POST', credentials: 'include' });
  showLoginOverlay();
});

// -- Dashboard ----------------------------------------------------------------
async function loadDashboard() {
  const data = await apiFetch('/admin/dashboard');
  if (!data) return;
  document.getElementById('stat-accounts').textContent  = data.accounts_created;
  document.getElementById('stat-referrers').textContent = data.total_referrers;

  const list = document.getElementById('top-referrers-list');
  if (!data.top_referrers.length) {
    list.innerHTML = '<div style="color:var(--text-muted);font-size:.875rem">No referrals yet</div>';
    return;
  }
  list.innerHTML = data.top_referrers.map(r =>
    `<div class="ref-row"><span>@${r.referrer}</span><span class="ref-count">${r.count} users</span></div>`
  ).join('');
}

// -- Users --------------------------------------------------------------------
let usersPage = 1;
const usersPageSize = 50;

async function loadUsers(page = 1) {
  usersPage = page;
  const search  = document.getElementById('filter-user-search').value.trim();
  const auth    = document.getElementById('filter-user-auth').value;
  const created = document.getElementById('filter-user-created').value;
  let url = `/admin/users?page=${page}&page_size=${usersPageSize}`;
  if (search)  url += `&search=${encodeURIComponent(search)}`;
  if (auth)    url += `&auth_provider=${encodeURIComponent(auth)}`;
  if (created !== '') url += `&account_created=${created}`;
  const data = await apiFetch(url);
  if (!data) return;

  const tbody = document.getElementById('users-tbody');
  if (!data.users.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted)">No users found</td></tr>';
  } else {
    tbody.innerHTML = data.users.map(u => `
      <tr>
        <td>${u.steem_username ? '@' + u.steem_username : '<em style="color:var(--text-muted)">pending</em>'}</td>
        <td style="font-size:.8rem;color:var(--text-muted)">${u.email || '-'}</td>
        <td>${u.auth_provider}</td>
        <td>${u.referrer ? '@' + u.referrer : '-'}</td>
        <td><span class="badge ${u.account_created ? 'badge-ok' : 'badge-pending'}">${u.account_created ? 'Yes' : 'No'}</span></td>
        <td>${u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</td>
        <td style="display:flex;gap:6px">
          <button class="btn btn-sm btn-secondary edit-user-btn" data-id="${u.id}" data-steem="${u.steem_username || ''}" data-referrer="${u.referrer || ''}">Edit</button>
          <button class="btn btn-sm btn-danger delete-user-btn" data-id="${u.id}" data-name="${u.steem_username || u.email || u.id}">Delete</button>
        </td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.edit-user-btn').forEach(btn => {
      btn.addEventListener('click', () => openEditUser(btn.dataset.id, btn.dataset.steem, btn.dataset.referrer));
    });

    tbody.querySelectorAll('.delete-user-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const name = btn.dataset.name;
        if (!confirm(`Delete user "${name}"? This cannot be undone.`)) return;
        try {
          await apiFetch(`/admin/users/${btn.dataset.id}`, 'DELETE');
          btn.closest('tr').remove();
        } catch (e) {
          alert('Error: ' + e.message);
        }
      });
    });
  }
  document.getElementById('users-page-info').textContent = `Page ${page} / ${Math.ceil(data.total / usersPageSize) || 1}`;
  document.getElementById('btn-users-prev').disabled = page <= 1;
  document.getElementById('btn-users-next').disabled = page * usersPageSize >= data.total;
}

document.getElementById('btn-filter-users').addEventListener('click', () => loadUsers(1));
document.getElementById('btn-users-prev').addEventListener('click', () => loadUsers(usersPage - 1));
document.getElementById('btn-users-next').addEventListener('click', () => loadUsers(usersPage + 1));

// -- Edit User Modal ----------------------------------------------------------
function openEditUser(id, steem, referrer) {
  document.getElementById('edit-user-id').value = id;
  document.getElementById('edit-user-steem').value = steem;
  document.getElementById('edit-user-referrer').value = referrer;
  document.getElementById('edit-user-err').textContent = '';
  const overlay = document.getElementById('edit-user-overlay');
  overlay.style.display = 'flex';
}

document.getElementById('btn-edit-user-cancel').addEventListener('click', () => {
  document.getElementById('edit-user-overlay').style.display = 'none';
});

document.getElementById('btn-edit-user-save').addEventListener('click', async () => {
  const id = document.getElementById('edit-user-id').value;
  const steem = document.getElementById('edit-user-steem').value.trim().toLowerCase();
  const referrer = document.getElementById('edit-user-referrer').value.trim().toLowerCase();
  const errEl = document.getElementById('edit-user-err');
  errEl.textContent = '';
  try {
    await apiFetch(`/admin/users/${id}`, 'PATCH', {
      steem_username: steem || null,
      referrer_steem: referrer || null,
    });
    document.getElementById('edit-user-overlay').style.display = 'none';
    loadUsers(usersPage);
  } catch (e) {
    errEl.textContent = e.message;
  }
});

// -- Referrer Settings --------------------------------------------------------
async function loadReferrerConfigs() {
  const data = await apiFetch('/admin/referrer-configs');
  if (!data) return;

  const tbody = document.getElementById('referrer-configs-tbody');
  if (!data.referrer_configs.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-muted)">No referrers yet</td></tr>';
    return;
  }

  tbody.innerHTML = data.referrer_configs.map(r => `
    <tr>
      <td><strong>@${r.steem_username}</strong></td>
      <td>${r.referred_count}</td>
      <td>
        <input type="number" class="inline-input pct-input" data-username="${r.steem_username}"
          value="${r.beneficiary_pct}" min="0" max="100" step="0.1" style="width:80px" />
        <span style="color:var(--text-muted);font-size:.8rem"> %</span>
      </td>
      <td>
        <input type="text" class="inline-input notes-input" data-username="${r.steem_username}"
          value="${r.notes || ''}" placeholder="optional notes..." style="width:180px" />
      </td>
      <td>
        <button class="btn btn-primary btn-sm save-referrer-cfg" data-username="${r.steem_username}">Save</button>
      </td>
    </tr>
  `).join('');

  document.querySelectorAll('.save-referrer-cfg').forEach(btn => {
    btn.addEventListener('click', async () => {
      const username = btn.dataset.username;
      const pct = parseFloat(document.querySelector(`.pct-input[data-username="${username}"]`).value);
      const notes = document.querySelector(`.notes-input[data-username="${username}"]`).value.trim() || null;
      try {
        await apiFetch(`/admin/referrer-configs/${username}`, 'PUT', { beneficiary_pct: pct, notes });
        btn.textContent = 'Saved!';
        btn.style.background = 'rgba(34,197,94,0.2)';
        setTimeout(() => { btn.textContent = 'Save'; btn.style.background = ''; }, 2000);
      } catch (e) {
        const msg = document.getElementById('referrer-configs-msg');
        msg.className = 'msg msg-err';
        msg.textContent = 'Error: ' + e.message;
      }
    });
  });
}

// -- Delegations --------------------------------------------------------------
async function loadDelegations() {
  const data = await apiFetch('/admin/delegations');
  if (!data) return;

  const tbody = document.getElementById('delegations-tbody');
  const withDelegation = data.delegations.filter(d => d.delegation_sp);

  const lastUpdate = data.delegations.find(d => d.delegation_updated_at)?.delegation_updated_at;
  document.getElementById('delegations-last-update').textContent =
    lastUpdate ? 'Last refresh: ' + new Date(lastUpdate).toLocaleString() : 'Never refreshed';

  if (!withDelegation.length) {
    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--text-muted)">No active delegations found. Click "Refresh" to fetch from chain.</td></tr>';
    return;
  }

  tbody.innerHTML = withDelegation.map(d => `
    <tr>
      <td>@${d.steem_username}</td>
      <td>${d.referrer ? '@' + d.referrer : '-'}</td>
      <td><strong>${d.delegation_sp.toFixed(3)} SP</strong></td>
      <td>${d.delegation_chain_time ? new Date(d.delegation_chain_time).toLocaleDateString() : '-'}</td>
      <td style="color:var(--text-muted);font-size:.8rem">${d.delegation_updated_at ? new Date(d.delegation_updated_at).toLocaleString() : '-'}</td>
    </tr>
  `).join('');
}

document.getElementById('btn-refresh-delegations').addEventListener('click', async () => {
  const btn = document.getElementById('btn-refresh-delegations');
  const msg = document.getElementById('delegations-msg');
  btn.disabled = true;
  btn.textContent = 'Refreshing...';
  msg.className = 'msg';
  msg.textContent = '';
  try {
    const result = await apiFetch('/admin/delegations/refresh', 'POST');
    msg.className = 'msg msg-ok';
    msg.textContent = `Updated ${result.updated} accounts${result.errors.length ? ` (${result.errors.length} errors)` : ''}`;
    loadDelegations();
  } catch (e) {
    msg.className = 'msg msg-err';
    msg.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Refresh from chain';
  }
});

// -- Initial load -------------------------------------------------------------
loadDashboard();
