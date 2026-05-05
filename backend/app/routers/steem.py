import logging
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from ..database import get_db
from ..models import JoinUser
from ..schemas import CreateAccountRequest, AccountKeysResponse
from ..steem_utils import (
    is_username_available,
    create_claimed_account,
    get_pending_claimed_accounts,
    account_exists_on_chain,
    validate_account_name,
)
from ..pdf_generator import generate_keys_pdf, generate_keys_txt
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/steem", tags=["steem"])


@router.get("/check-username/{username}")
async def check_username(username: str):
    """Check if a Steem username is available on chain."""
    username = username.lower().strip()
    err = validate_account_name(username)
    if err:
        return {"available": False, "username": username, "reason": err}
    try:
        available = is_username_available(username)
        return {"available": available, "username": username}
    except Exception as e:
        logger.error(f"check_username error: {e}")
        raise HTTPException(status_code=503, detail="Unable to check username, try again")


@router.get("/claimed-accounts")
async def claimed_accounts_count():
    """How many pre-claimed account tickets cur8 has available."""
    return {"pending_claimed_accounts": get_pending_claimed_accounts()}


@router.post("/create-account", response_model=AccountKeysResponse)
async def create_account(
    req: CreateAccountRequest,
    db: Session = Depends(get_db),
    current_user: JoinUser = Depends(get_current_user),
):
    """
    Create a Steem account using a claimed account ticket.
    Keys are returned ONCE and never stored.
    """
    # Rate limit: one account per auth user
    if current_user.account_created:
        raise HTTPException(status_code=409, detail="You have already created an account")

    username = req.username.lower().strip()

    # Validate username format
    format_err = validate_account_name(username)
    if format_err:
        raise HTTPException(status_code=400, detail=format_err)

    # Check availability
    if not is_username_available(username):
        raise HTTPException(status_code=409, detail="Username already taken")

    # Validate referrer exists on chain
    referrer = req.referrer or current_user.referrer_steem
    if referrer and not account_exists_on_chain(referrer):
        referrer = None  # silently drop invalid referrer

    # Check ticket availability
    tickets = get_pending_claimed_accounts()
    if tickets < 1:
        raise HTTPException(status_code=503, detail="No claimed account tickets available, try again later")

    # Create account on chain
    try:
        keys = create_claimed_account(username)
    except Exception as e:
        logger.error(f"Account creation failed for {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Account creation failed: {str(e)}")

    # Update user record — store only the username and referrer, NEVER the keys
    current_user.steem_username = username
    current_user.account_created = True
    if referrer:
        current_user.referrer_steem = referrer
    db.commit()

    return keys


@router.post("/keys/download/pdf")
async def download_keys_pdf(keys: AccountKeysResponse):
    """Generate and stream a PDF with account credentials."""
    pdf_bytes = generate_keys_pdf(keys.username, keys.dict())
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{keys.username}-steem-keys.pdf"'},
    )


@router.post("/keys/download/txt")
async def download_keys_txt(keys: AccountKeysResponse):
    """Generate and stream a TXT file with account credentials."""
    txt = generate_keys_txt(keys.username, keys.dict())
    return StreamingResponse(
        io.BytesIO(txt.encode()),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{keys.username}-steem-keys.txt"'},
    )
