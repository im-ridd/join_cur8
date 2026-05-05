const API = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8002'
  : '';

// ── Load keys from sessionStorage ────────────────────────────────────────────
const keysRaw = sessionStorage.getItem('steem_keys');
let keys = null;
if (keysRaw) {
  try { keys = JSON.parse(keysRaw); } catch (_) {}
}

if (!keys) {
  // Keys are gone (already viewed or navigated directly) — show static message
  document.getElementById('keys-section').classList.add('hidden');
  document.getElementById('already-created-msg').classList.remove('hidden');
} else {

// ── Populate UI ───────────────────────────────────────────────────────────────
document.getElementById('username-display').textContent = '@' + keys.username;
document.getElementById('val-master').textContent  = keys.master_password;
document.getElementById('val-posting').textContent = keys.posting_key;
document.getElementById('val-active').textContent  = keys.active_key;
document.getElementById('val-owner').textContent   = keys.owner_key;
document.getElementById('val-memo').textContent    = keys.memo_key;

// ── Copy buttons ──────────────────────────────────────────────────────────────
document.querySelectorAll('.btn-copy').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = document.getElementById(btn.dataset.target);
    navigator.clipboard.writeText(target.textContent).then(() => {
      btn.textContent = '✅';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = '📋'; btn.classList.remove('copied'); }, 2000);
    });
  });
});

// ── Downloads ─────────────────────────────────────────────────────────────────
document.getElementById('btn-download-txt').addEventListener('click', () => {
  const lines = [
    `cur8 / Steem Account Keys`,
    `Generated: ${new Date().toISOString()}`,
    `Username: @${keys.username}`,
    ``,
    `MASTER PASSWORD`,
    keys.master_password,
    ``,
    `POSTING KEY (day-to-day: posts, votes, comments)`,
    keys.posting_key,
    ``,
    `ACTIVE KEY (transfers, power-ups, wallet)`,
    keys.active_key,
    ``,
    `OWNER KEY (account recovery — store offline)`,
    keys.owner_key,
    ``,
    `MEMO KEY (encrypted transfer memos)`,
    keys.memo_key,
    ``,
    `WARNING: Keep these keys private. Anyone with your keys controls your account.`,
  ].join('\n');
  const blob = new Blob([lines], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${keys.username}-steem-keys.txt`;
  a.click();
  URL.revokeObjectURL(url);
});

// ── Confirm saved checkbox → show next steps ──────────────────────────────────
document.getElementById('confirm-saved').addEventListener('change', function () {
  const nextSteps = document.getElementById('next-steps');
  if (this.checked) {
    nextSteps.classList.remove('hidden');
    // Clear keys from sessionStorage now that user confirmed
    sessionStorage.removeItem('steem_keys');
  } else {
    nextSteps.classList.add('hidden');
  }
});

} // end if (keys)
