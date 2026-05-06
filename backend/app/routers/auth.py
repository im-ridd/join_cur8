import os
import uuid
import secrets as _secrets
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import JoinUser
from ..schemas import EmailRegisterRequest, EmailVerifyOTPRequest
from ..email_utils import validate_email_address
from ..steem_utils import account_exists_on_chain


def _validate_referrer(referrer: Optional[str]) -> Optional[str]:
    """Return cleaned referrer if it exists on Steem chain, else None."""
    if not referrer:
        return None
    ref = referrer.strip().lower()
    try:
        if account_exists_on_chain(ref):
            return ref
    except Exception:
        pass
    return None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# ── JWT ──────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> JoinUser:
    token = request.cookies.get("join_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(JoinUser).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _set_token_cookie(response: Response, user_id: str):
    token = create_token(user_id)
    response.set_cookie(
        key="join_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        max_age=JWT_EXPIRE_DAYS * 86400,
    )


# ── Google OAuth ──────────────────────────────────────────────────────────────
def _get_oauth():
    """Lazy init so credentials are read from env at request time."""
    o = OAuth()
    o.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    return o


@router.get("/google/login")
async def google_login(request: Request, referrer: Optional[str] = None):
    if referrer:
        request.session["oauth_referrer"] = referrer
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8002/auth/google/callback")
    return await _get_oauth().google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        token = await _get_oauth().google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        return RedirectResponse(url=f"{frontend_url}/?auth_error=google_failed")

    userinfo = token.get("userinfo") or {}
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    referrer = _validate_referrer(request.session.pop("oauth_referrer", None))

    if not google_id:
        raise HTTPException(status_code=400, detail="Could not get Google user info")

    user = db.query(JoinUser).filter_by(auth_provider="google", auth_id=google_id).first()
    if not user:
        user = JoinUser(
            id=str(uuid.uuid4()),
            auth_provider="google",
            auth_id=google_id,
            email=email,
            referrer_steem=referrer,
        )
        db.add(user)
    else:
        # Update referrer for existing users who don't have one yet
        if referrer and not user.referrer_steem:
            user.referrer_steem = referrer
    user.last_login = datetime.utcnow()
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
    if user.account_created:
        redirect_url = f"{frontend_url}/?already_created=1"
    else:
        redirect_url = f"{frontend_url}/?create=1"
    redirect = RedirectResponse(url=redirect_url)
    _set_token_cookie(redirect, user.id)
    return redirect


# ── Email OTP ─────────────────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@cur8.fun")
OTP_EXPIRE_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60


def _send_otp_email(to_email: str, code: str):
    if not SMTP_HOST:
        logger.info(f"[DEV] Email OTP for {to_email}: {code}")
        return
    msg = MIMEText(
        f"Your cur8 verification code is:\n\n  {code}\n\nValid for {OTP_EXPIRE_MINUTES} minutes.\n\nIf you didn't request this, ignore this email."
    )
    msg["Subject"] = f"{code} is your cur8 verification code"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


@router.post("/email/send-otp")
async def email_send_otp(req: EmailRegisterRequest, db: Session = Depends(get_db)):
    # Validate email format, check for disposable domains and MX record
    email_err = validate_email_address(req.email)
    if email_err:
        raise HTTPException(status_code=422, detail=email_err)

    # Block if same email was used via another provider (e.g. Google)
    other_provider = db.query(JoinUser).filter(
        JoinUser.email == req.email,
        JoinUser.auth_provider != "email"
    ).first()
    if other_provider:
        if other_provider.account_created:
            raise HTTPException(
                status_code=409,
                detail="A Steem account has already been created with this email."
            )
        else:
            raise HTTPException(
                status_code=409,
                detail="This email was already used to start registration. Please complete it using the original sign-in method."
            )

    existing = db.query(JoinUser).filter_by(auth_provider="email", auth_id=req.email).first()
    if existing and existing.account_created:
        raise HTTPException(status_code=409, detail="A Steem account has already been created with this email")

    # Rate limit: block resend if last OTP was sent less than 60s ago
    if existing and existing.email_otp_expires:
        otp_sent_at = existing.email_otp_expires - timedelta(minutes=OTP_EXPIRE_MINUTES)
        seconds_since = (datetime.utcnow() - otp_sent_at).total_seconds()
        if seconds_since < OTP_RESEND_COOLDOWN_SECONDS:
            wait = int(OTP_RESEND_COOLDOWN_SECONDS - seconds_since)
            raise HTTPException(status_code=429, detail=f"Please wait {wait}s before requesting a new code")

    code = f"{_secrets.randbelow(1000000):06d}"
    expires = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)

    if existing:
        existing.email_otp = code
        existing.email_otp_expires = expires
    else:
        existing = JoinUser(
            id=str(uuid.uuid4()),
            auth_provider="email",
            auth_id=req.email,
            email=req.email,
            referrer_steem=_validate_referrer(req.referrer),
            email_otp=code,
            email_otp_expires=expires,
        )
        db.add(existing)
    db.commit()

    try:
        _send_otp_email(req.email, code)
    except Exception as e:
        logger.error(f"Failed to send OTP email to {req.email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"message": "Verification code sent"}


@router.post("/email/verify-otp")
async def email_verify_otp(req: EmailVerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(JoinUser).filter_by(auth_provider="email", auth_id=req.email).first()
    if not user or not user.email_otp:
        raise HTTPException(status_code=400, detail="No verification pending for this email")
    if datetime.utcnow() > user.email_otp_expires:
        raise HTTPException(status_code=400, detail="Verification code expired, request a new one")
    if user.email_otp != req.code.strip():
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.email_otp = None
    user.email_otp_expires = None
    user.last_login = datetime.utcnow()
    db.commit()

    resp = JSONResponse({"message": "Email verified"})
    _set_token_cookie(resp, user.id)
    return resp


@router.post("/logout")
async def logout():
    resp = JSONResponse({"message": "Logged out"})
    resp.delete_cookie("join_token")
    return resp


@router.get("/me")
async def me(current_user: JoinUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "steem_username": current_user.steem_username,
        "auth_provider": current_user.auth_provider,
        "referrer_steem": current_user.referrer_steem,
        "account_created": current_user.account_created,
    }
