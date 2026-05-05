import os
import re
import secrets
import string
import logging
import httpx

logger = logging.getLogger(__name__)

try:
    from beem import Steem
    from beemgraphenebase.account import PasswordKey
    from beembase.operations import Create_claimed_account
    BEEM_AVAILABLE = True
except ImportError:
    BEEM_AVAILABLE = False
    logger.warning("beem not installed — Steem account creation will be unavailable")

STEEM_NODES = [
    "https://api.moecki.online",
    "https://api.steemit.com",
    "https://steemapi.boylikegirl.club",
    "https://api.pennsif.net",
]

CREATOR_ACCOUNT = os.getenv("STEEM_CREATOR_ACCOUNT", "cur8")
CREATOR_ACTIVE_KEY = os.getenv("STEEM_ACTIVE_KEY", "")


def validate_account_name(name: str) -> str | None:
    """Returns an error message string if invalid, None if valid."""
    if not name:
        return "Username cannot be empty"
    if len(name) < 3:
        return "Too short (min 3 characters)"
    if len(name) > 16:
        return "Too long (max 16 characters)"
    if re.search(r'[^a-z0-9-]', name):
        return "Only lowercase letters, digits and hyphens allowed"
    if re.match(r'^[^a-z]', name):
        return "Must start with a letter"
    if re.search(r'[^a-z0-9]$', name):
        return "Must end with a letter or digit"
    if '--' in name:
        return "Cannot contain consecutive hyphens (--)"
    return None


def _get_steem_client():
    if not BEEM_AVAILABLE:
        raise RuntimeError("beem library not available")
    return Steem(node=STEEM_NODES, keys=[CREATOR_ACTIVE_KEY], nobroadcast=False)


def generate_master_password(length: int = 52) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def derive_keys(username: str, master_password: str) -> dict:
    """Derive all Steem keys from username + master password."""
    if not BEEM_AVAILABLE:
        raise RuntimeError("beem library not available")
    roles = ["owner", "active", "posting", "memo"]
    keys = {}
    for role in roles:
        pk = PasswordKey(username, master_password, role=role)
        private = pk.get_private_key()
        keys[f"{role}_private"] = str(private)
        keys[f"{role}_public"] = str(private.get_public_key())
    return keys


def _rpc_get_accounts(usernames: list) -> list:
    """Public RPC call — no keys required."""
    for node in STEEM_NODES:
        try:
            resp = httpx.post(
                node,
                json={"jsonrpc": "2.0", "method": "condenser_api.get_accounts", "params": [usernames], "id": 1},
                timeout=5,
            )
            result = resp.json().get("result", [])
            return result
        except Exception as e:
            logger.warning(f"RPC node {node} failed: {e}")
    raise RuntimeError("All Steem RPC nodes unreachable")


def is_username_available(username: str) -> bool:
    """Return True if the username is not yet registered on chain."""
    accounts = _rpc_get_accounts([username])
    return len(accounts) == 0 or accounts[0] is None


def account_exists_on_chain(username: str) -> bool:
    """Return True if an account already exists on-chain (used to validate referrers)."""
    accounts = _rpc_get_accounts([username])
    return len(accounts) > 0 and accounts[0] is not None




def get_pending_claimed_accounts() -> int:
    """Return how many pending claimed accounts cur8 has."""
    try:
        steem = _get_steem_client()
        accounts = steem.rpc.get_accounts([CREATOR_ACCOUNT])
        if not accounts:
            return 0
        return int(accounts[0].get("pending_claimed_accounts", 0))
    except Exception as e:
        logger.error(f"Error fetching pending claimed accounts: {e}")
        return 0


def create_claimed_account(username: str) -> dict:
    """
    Create a Steem account using a pre-claimed account ticket on cur8.
    Returns the generated keys (master password + all private keys).
    Keys are NEVER stored in the database — caller must deliver them to the user immediately.
    """
    if not CREATOR_ACTIVE_KEY:
        raise ValueError("STEEM_ACTIVE_KEY not configured")

    master_password = generate_master_password()
    keys = derive_keys(username, master_password)

    steem = _get_steem_client()

    op = Create_claimed_account(**{
        "creator": CREATOR_ACCOUNT,
        "new_account_name": username,
        "owner": {
            "weight_threshold": 1,
            "account_auths": [],
            "key_auths": [[keys["owner_public"], 1]],
        },
        "active": {
            "weight_threshold": 1,
            "account_auths": [],
            "key_auths": [[keys["active_public"], 1]],
        },
        "posting": {
            "weight_threshold": 1,
            "account_auths": [],
            "key_auths": [[keys["posting_public"], 1]],
        },
        "memo_key": keys["memo_public"],
        "json_metadata": '{"created_by":"cur8","app":"join.cur8.fun"}',
        "extensions": [],
    })

    steem.finalizeOp(op, CREATOR_ACCOUNT, "active")

    return {
        "username": username,
        "master_password": master_password,
        "owner_key": keys["owner_private"],
        "active_key": keys["active_private"],
        "posting_key": keys["posting_private"],
        "memo_key": keys["memo_private"],
    }


def _rpc_call(method: str, params) -> object:
    """Generic RPC call, tries all nodes."""
    for node in STEEM_NODES:
        try:
            resp = httpx.post(
                node,
                json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
                timeout=10,
            )
            result = resp.json()
            if "result" in result:
                return result["result"]
        except Exception as e:
            logger.warning(f"RPC node {node} failed ({method}): {e}")
    raise RuntimeError(f"All Steem RPC nodes unreachable for {method}")


def get_delegation_to_cur8(username: str) -> tuple[float, object]:
    """Get how much SP username has delegated to cur8, and when they last updated it.
    Returns (sp, chain_datetime).
    sp is the current delegation amount.
    chain_datetime is taken from the last delegate_vesting_shares op in account history."""
    from datetime import datetime as dt

    sp = 0.0
    chain_time = None

    # 1. Get current delegation amount
    try:
        delegations = _rpc_call(
            "condenser_api.get_vesting_delegations",
            [username, "cur8", 100]
        )
        for d in delegations or []:
            if d.get("delegatee") == "cur8":
                vests = float(d["vesting_shares"].split()[0])
                props = _rpc_call("condenser_api.get_dynamic_global_properties", [])
                total_vests = float(props["total_vesting_shares"].split()[0])
                total_sp = float(props["total_vesting_fund_steem"].split()[0])
                sp = round(vests * total_sp / total_vests, 3)
                break
    except Exception as e:
        logger.error(f"Error fetching delegation amount for {username}: {e}")

    # 2. Find last delegate_vesting_shares → cur8 in account history
    # Use operation_filter_low bitmask: delegate_vesting_shares = op type 40 → 1 << 40
    DELEGATE_OP_MASK = 1 << 40
    try:
        ops = _rpc_call(
            "account_history_api.get_account_history",
            {
                "account": username,
                "start": -1,
                "limit": 1000,
                "operation_filter_low": DELEGATE_OP_MASK,
            }
        )
        history = ops.get("history", []) if isinstance(ops, dict) else []
        for _seq, op in reversed(history):
            op_data = op.get("op", {}).get("value", {})
            if op_data.get("delegatee") == "cur8":
                raw = op.get("timestamp")
                if raw:
                    try:
                        chain_time = dt.strptime(raw, "%Y-%m-%dT%H:%M:%S")
                    except Exception:
                        pass
                break
    except Exception as e:
        logger.error(f"Error fetching account history for {username}: {e}")

    return sp, chain_time
