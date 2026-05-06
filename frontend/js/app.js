const API = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8002'
  : '';  // production: same origin via nginx proxy

// ── Referral from URL path or ?ref= query param ───────────────────────────
(function detectReferrer() {
  // Priority 1: ?ref=name query param (works with any static server)
  const qref = new URLSearchParams(window.location.search).get('ref');
  if (qref) { sessionStorage.setItem('referrer', qref.toLowerCase()); return; }
  // Priority 2: /name path (works in production with nginx catch-all)
  const path = window.location.pathname.replace(/^\//, '').replace(/\/$/, '').trim();
  if (path && path !== 'index.html' && !/\.html?$/.test(path)) {
    sessionStorage.setItem('referrer', path.toLowerCase()); return;
  }
  // Returning from OAuth (?create=1 or ?already_created=1): preserve stored referrer
  const params = new URLSearchParams(window.location.search);
  if (params.get('create') || params.get('already_created')) return;
  // No ref in URL and not returning from OAuth → clear stored referrer
  sessionStorage.removeItem('referrer');
})();

function getReferrer() {
  // Always read from the visible input field if present
  const inp = document.getElementById('referrer-input');
  if (inp) return inp.value.trim();
  return sessionStorage.getItem('referrer') || '';
}

// ── DOM refs ──────────────────────────────────────────────────────────────────
const authSection   = document.getElementById('auth-section');
const createSection = document.getElementById('create-section');
const loadingEl     = document.getElementById('loading');
const authError     = document.getElementById('auth-error');
const createError   = document.getElementById('create-error');const referrerError = document.getElementById('referrer-error');
// ── Show referrer badge + pre-fill input ──────────────────────────────────────
const ref = sessionStorage.getItem('referrer') || '';
if (ref) {
  document.getElementById('referrer-name').textContent = '@' + ref;
  document.getElementById('referrer-badge').classList.remove('hidden');
  const inp = document.getElementById('referrer-input');
  if (inp) inp.value = ref;
}

// ── Utility ───────────────────────────────────────────────────────────────────
function showError(el, msg) {
  el.textContent = msg;
  el.classList.remove('hidden');
}
function clearError(el) { el.classList.add('hidden'); }

function setLoading(on) {
  loadingEl.classList.toggle('hidden', !on);
  authSection.classList.toggle('hidden', on);
  createSection.classList.toggle('hidden', on || createSection._wasHidden);
}

async function api(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg;
    if (Array.isArray(data.detail)) {
      // Pydantic validation errors — pick the first message
      msg = data.detail[0]?.msg || res.statusText;
      // Clean up "Value error, " prefix added by Pydantic v2
      msg = msg.replace(/^value error,\s*/i, '');
    } else {
      msg = data.detail || res.statusText;
    }
    throw new Error(msg);
  }
  return data;
}

function showCreateSection() {
  authSection.classList.add('hidden');
  createSection.classList.remove('hidden');
  createSection._wasHidden = false;
}

function showAlreadyCreated() {
  authSection.classList.add('hidden');
  document.getElementById('already-created-section').classList.remove('hidden');
}

// Check URL params set by OAuth callback
const _urlParams = new URLSearchParams(window.location.search);
if (_urlParams.get('already_created')) {
  showAlreadyCreated();
} else if (_urlParams.get('create')) {
  // Verify session is real before showing create section
  api('/auth/me').then(user => {
    if (user && !user.account_created) {
      showCreateSection();
    } else if (user && user.account_created) {
      showAlreadyCreated();
    }
    // If api throws (401), stays on auth section — no action needed
  }).catch(() => {
    // Invalid/missing session: clean URL and stay on auth page
    history.replaceState(null, '', '/');
  });
}

// ── Google OAuth ──────────────────────────────────────────────────────────────
function checkReferrerBeforeAuth() {
  const val = document.getElementById('referrer-input').value.trim();
  if (!val) return true; // empty = OK
  const status = document.getElementById('referrer-input').dataset.valid;
  if (status === 'false') {
    showError(referrerError, `"@${val}" does not exist on Steem. Leave it empty or enter a valid username.`);
    return false;
  }
  if (status !== 'true') {
    showError(referrerError, 'Validating referrer… please wait a moment and try again.');
    return false;
  }
  return true;
}

document.getElementById('btn-google').addEventListener('click', () => {
  if (!checkReferrerBeforeAuth()) return;
  const ref = getReferrer();
  window.location.href = `${API}/auth/google/login${ref ? '?referrer=' + encodeURIComponent(ref) : ''}`;
});

// ── Email OTP ─────────────────────────────────────────────────────────────────
let otpCooldownTimer = null;

function startOtpCooldown() {
  const btn = document.getElementById('btn-email-register');
  let seconds = 60;
  btn.disabled = true;
  btn.textContent = `Resend in ${seconds}s`;
  clearInterval(otpCooldownTimer);
  otpCooldownTimer = setInterval(() => {
    seconds--;
    if (seconds <= 0) {
      clearInterval(otpCooldownTimer);
      btn.disabled = false;
      btn.textContent = 'Resend code';
    } else {
      btn.textContent = `Resend in ${seconds}s`;
    }
  }, 1000);
}

document.getElementById('btn-email-register').addEventListener('click', async () => {
  clearError(authError);
  clearError(referrerError);
  if (!checkReferrerBeforeAuth()) return;
  const email = document.getElementById('email-input').value.trim();
  if (!email) return showError(authError, 'Please enter your email address');

  // Show OTP row immediately for instant feedback
  document.getElementById('email-otp-row').classList.remove('hidden');
  document.getElementById('email-input').disabled = true;
  document.getElementById('email-otp-input').focus();
  startOtpCooldown();

  try {
    await api('/auth/email/send-otp', 'POST', { email, referrer: getReferrer() || null });
  } catch (e) {
    // Revert UI on failure
    document.getElementById('email-otp-row').classList.add('hidden');
    document.getElementById('email-input').disabled = false;
    clearInterval(otpCooldownTimer);
    const btn = document.getElementById('btn-email-register');
    btn.disabled = false;
    btn.textContent = 'Continue with Email';
    showError(authError, e.message);
  }
});

document.getElementById('btn-email-verify').addEventListener('click', async () => {
  clearError(authError);
  const email = document.getElementById('email-input').value.trim();
  const code  = document.getElementById('email-otp-input').value.trim();
  if (!code) return showError(authError, 'Please enter the verification code');
  try {
    await api('/auth/email/verify-otp', 'POST', { email, code });
    showCreateSection();
  } catch (e) {
    if (e.message.includes('already been created')) {
      showAlreadyCreated();
    } else {
      showError(authError, e.message);
    }
  }
});

document.getElementById('email-otp-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('btn-email-verify').click();
});

// ── Steem account name validation (mirrors steem-js rules) ───────────────────
function validateSteemUsername(name) {
  if (!name) return 'Username cannot be empty';
  if (name.length < 3) return 'Too short (min 3 characters)';
  if (name.length > 16) return 'Too long (max 16 characters)';
  if (/[^a-z0-9-]/.test(name)) return 'Only lowercase letters, digits and hyphens allowed';
  if (/^[^a-z]/.test(name)) return 'Must start with a letter';
  if (/[^a-z0-9]$/.test(name)) return 'Must end with a letter or digit';
  if (/--/.test(name)) return 'Cannot contain consecutive hyphens (--)';
  return null; // valid
}

// ── Username availability check ───────────────────────────────────────────────
let usernameTimer = null;
const usernameInput  = document.getElementById('username-input');
const usernameStatus = document.getElementById('username-status');
const createBtn      = document.getElementById('btn-create');

usernameInput.addEventListener('input', () => {
  clearTimeout(usernameTimer);
  const val = usernameInput.value.toLowerCase().trim();
  usernameInput.value = val;
  usernameStatus.textContent = '';
  createBtn.disabled = true;
  clearError(createError);

  if (!val) return;

  const formatErr = validateSteemUsername(val);
  if (formatErr) {
    usernameStatus.textContent = '❌';
    showError(createError, formatErr);
    return;
  }

  usernameStatus.textContent = '⏳';
  usernameTimer = setTimeout(async () => {
    try {
      const data = await api(`/api/steem/check-username/${val}`);
      if (data.available) {
        usernameStatus.textContent = '✅';
        createBtn.disabled = false;
      } else {
        usernameStatus.textContent = '❌';
        showError(createError, data.reason || 'Username already taken');
      }
    } catch (e) {
      usernameStatus.textContent = '⚠️';
    }
  }, 600);
});

// ── Referrer validation ───────────────────────────────────────────────────────
let referrerTimer = null;
const referrerInput  = document.getElementById('referrer-input');
const referrerStatus = document.getElementById('referrer-status');

referrerInput.addEventListener('input', () => {
  clearTimeout(referrerTimer);
  const val = referrerInput.value.toLowerCase().trim();
  referrerInput.value = val;
  referrerStatus.textContent = '';
  referrerInput.dataset.valid = '';
  clearError(referrerError);
  if (!val) return;
  referrerStatus.textContent = '⏳';
  referrerTimer = setTimeout(() => validateReferrer(val), 600);
});

async function validateReferrer(val) {
  try {
    const data = await api(`/api/steem/check-username/${val}`);
    if (referrerInput.value.trim() !== val) return; // input changed meanwhile
    // available=true → account free (doesn't exist); reason set → invalid format
    // Both cases mean it's NOT a valid referrer
    if (data.available || data.reason) {
      referrerStatus.textContent = '❌';
      referrerInput.dataset.valid = 'false';
    } else {
      referrerStatus.textContent = '✅';
      referrerInput.dataset.valid = 'true';
    }
  } catch (e) {
    referrerStatus.textContent = '⚠️';
  }
}

// If pre-filled from URL, validate immediately (listener is now registered)
if (referrerInput.value.trim()) {
  referrerStatus.textContent = '⏳';
  validateReferrer(referrerInput.value.trim());
}

// ── Create Steem Account ──────────────────────────────────────────────────────
createBtn.addEventListener('click', async () => {
  const username = usernameInput.value.trim();
  if (!username) return;

  // Validate referrer if filled in
  const referrerVal = referrerInput.value.trim();
  if (referrerVal && referrerInput.dataset.valid === 'false') {
    return showError(createError, `Referrer "@${referrerVal}" does not exist on Steem`);
  }
  if (referrerVal && referrerInput.dataset.valid !== 'true') {
    return showError(createError, 'Please wait for referrer validation to complete');
  }

  clearError(createError);
  createSection.classList.add('hidden');
  createSection._wasHidden = true;
  setLoading(true);

  try {
    const keys = await api('/api/steem/create-account', 'POST', {
      username,
      referrer: referrerVal || null,
    });

    // Store keys in sessionStorage for success page (only for current session)
    sessionStorage.setItem('steem_keys', JSON.stringify(keys));
    window.location.href = '/success.html';
  } catch (e) {
    setLoading(false);
    createSection._wasHidden = false;
    createSection.classList.remove('hidden');
    showError(createError, e.message);
  }
});
