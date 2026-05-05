import os
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db, get_config, set_config
from ..models import JoinUser, ReferrerConfig, PlatformConfig
from ..schemas import AdminLoginRequest, ConfigUpdateRequest, ReferrerConfigUpdate
from ..steem_utils import get_delegation_to_cur8

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_admin(request: Request):
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


AdminDep = Depends(verify_admin)


# ── Admin UI pages ─────────────────────────────────────────────────────────────
_ADMIN_INDEX = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "admin", "index.html")
)


@router.get("/", response_class=FileResponse, include_in_schema=False)
async def admin_ui_root():
    return FileResponse(_ADMIN_INDEX)


@router.get("/login", response_class=FileResponse, include_in_schema=False)
async def admin_ui_login():
    return FileResponse(_ADMIN_INDEX)


@router.post("/login")
async def admin_login(req: AdminLoginRequest):
    if req.username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    expected = os.getenv("ADMIN_PASSWORD_HASH", "")
    if expected:
        if not pwd_context.verify(req.password, expected):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        if req.password != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({"sub": req.username, "role": "admin"}, SECRET_KEY, algorithm=ALGORITHM)
    resp = JSONResponse({"message": "Login successful"})
    resp.set_cookie(
        "admin_token", token, httponly=True, samesite="lax",
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    )
    return resp


@router.post("/logout")
async def admin_logout():
    resp = JSONResponse({"message": "Logged out"})
    resp.delete_cookie("admin_token")
    return resp


# ── Dashboard ──────────────────────────────────────────────────────────────────
@router.get("/dashboard")
async def dashboard(db: Session = Depends(get_db), _=AdminDep):
    accounts_created = db.query(JoinUser).filter_by(account_created=True).count()
    total_referrers = (
        db.query(JoinUser.referrer_steem)
        .filter(JoinUser.referrer_steem.isnot(None))
        .distinct()
        .count()
    )

    top_referrers = (
        db.query(JoinUser.referrer_steem, func.count(JoinUser.id).label("count"))
        .filter(JoinUser.referrer_steem.isnot(None))
        .group_by(JoinUser.referrer_steem)
        .order_by(func.count(JoinUser.id).desc())
        .limit(10)
        .all()
    )

    return {
        "accounts_created": accounts_created,
        "total_referrers": total_referrers,
        "top_referrers": [{"referrer": r, "count": c} for r, c in top_referrers],
    }


# ── Users ──────────────────────────────────────────────────────────────────────
@router.get("/users")
async def list_users(
    search: Optional[str] = None,
    auth_provider: Optional[str] = None,
    account_created: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _=AdminDep,
):
    query = db.query(JoinUser)
    if search:
        query = query.filter(
            JoinUser.steem_username.ilike(f"%{search}%") |
            JoinUser.email.ilike(f"%{search}%")
        )
    if auth_provider:
        query = query.filter(JoinUser.auth_provider == auth_provider)
    if account_created is not None:
        query = query.filter(JoinUser.account_created == account_created)
    total = query.count()
    users = query.order_by(JoinUser.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": [
            {
                "id": u.id,
                "steem_username": u.steem_username,
                "email": u.email,
                "auth_provider": u.auth_provider,
                "referrer": u.referrer_steem,
                "account_created": u.account_created,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.patch("/users/{user_id}")
async def update_user(user_id: str, req: dict, db: Session = Depends(get_db), _=AdminDep):
    from pydantic import BaseModel
    user = db.query(JoinUser).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "referrer_steem" in req:
        val = req["referrer_steem"].strip().lower() if req["referrer_steem"] else None
        user.referrer_steem = val or None
    if "steem_username" in req:
        val = req["steem_username"].strip().lower() if req["steem_username"] else None
        user.steem_username = val or None
    db.commit()
    return {
        "id": user.id,
        "steem_username": user.steem_username,
        "referrer": user.referrer_steem,
    }


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db), _=AdminDep):
    user = db.query(JoinUser).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"deleted": user_id}


# ── Referrals ──────────────────────────────────────────────────────────────────
@router.get("/referrals")
async def list_referrals(
    referrer: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _=AdminDep,
):
    query = db.query(JoinUser).filter(JoinUser.referrer_steem.isnot(None))
    if referrer:
        query = query.filter(JoinUser.referrer_steem == referrer)
    total = query.count()
    users = query.order_by(JoinUser.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "referrals": [
            {
                "id": u.id,
                "steem_username": u.steem_username,
                "referrer_steem": u.referrer_steem,
                "auth_provider": u.auth_provider,
                "account_created": u.account_created,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


# ── Referrer Configs (per-referrer beneficiary %) ──────────────────────────────
@router.get("/referrer-configs")
async def list_referrer_configs(db: Session = Depends(get_db), _=AdminDep):
    """All known referrers with their beneficiary % (falls back to global default)."""
    referrers_in_db = (
        db.query(JoinUser.referrer_steem, func.count(JoinUser.id).label("referred_count"))
        .filter(JoinUser.referrer_steem.isnot(None))
        .group_by(JoinUser.referrer_steem)
        .order_by(func.count(JoinUser.id).desc())
        .all()
    )
    configs = {c.steem_username: c for c in db.query(ReferrerConfig).all()}
    default_pct = float(get_config(db, "default_beneficiary_pct", "10.0"))

    result = []
    for referrer, count in referrers_in_db:
        cfg = configs.get(referrer)
        result.append({
            "steem_username": referrer,
            "referred_count": count,
            "beneficiary_pct": cfg.beneficiary_pct if cfg else default_pct,
            "notes": cfg.notes if cfg else None,
            "updated_at": cfg.updated_at.isoformat() if cfg and cfg.updated_at else None,
        })

    return {"referrer_configs": result, "default_pct": default_pct}


@router.put("/referrer-configs/{steem_username}")
async def upsert_referrer_config(
    steem_username: str,
    req: ReferrerConfigUpdate,
    db: Session = Depends(get_db),
    _=AdminDep,
):
    steem_username = steem_username.lower().strip()
    if req.beneficiary_pct < 0 or req.beneficiary_pct > 100:
        raise HTTPException(status_code=422, detail="beneficiary_pct must be between 0 and 100")

    cfg = db.query(ReferrerConfig).filter_by(steem_username=steem_username).first()
    if cfg:
        cfg.beneficiary_pct = req.beneficiary_pct
        cfg.notes = req.notes
        cfg.updated_at = datetime.utcnow()
    else:
        cfg = ReferrerConfig(
            steem_username=steem_username,
            beneficiary_pct=req.beneficiary_pct,
            notes=req.notes,
        )
        db.add(cfg)
    db.commit()
    return {"steem_username": steem_username, "beneficiary_pct": cfg.beneficiary_pct, "notes": cfg.notes}


# ── Delegations (read-only, cached) ───────────────────────────────────────────
@router.get("/delegations")
async def list_delegations(db: Session = Depends(get_db), _=AdminDep):
    """Return cached delegation data for all users with Steem accounts."""
    users = (
        db.query(JoinUser)
        .filter(JoinUser.steem_username.isnot(None), JoinUser.account_created == True)  # noqa: E712
        .order_by(JoinUser.delegation_sp.desc().nullslast())
        .all()
    )
    return {
        "delegations": [
            {
                "steem_username": u.steem_username,
                "referrer": u.referrer_steem,
                "delegation_sp": u.delegation_sp,
                "delegation_chain_time": u.delegation_chain_time.isoformat() if u.delegation_chain_time else None,
                "delegation_updated_at": u.delegation_updated_at.isoformat() if u.delegation_updated_at else None,
            }
            for u in users
        ]
    }


@router.post("/delegations/refresh")
async def refresh_delegations(db: Session = Depends(get_db), _=AdminDep):
    """Fetch current delegation amounts from Steem chain and update cache."""
    users = (
        db.query(JoinUser)
        .filter(JoinUser.steem_username.isnot(None), JoinUser.account_created == True)  # noqa: E712
        .all()
    )
    updated = 0
    errors = []
    now = datetime.utcnow()

    for u in users:
        try:
            sp, chain_time = get_delegation_to_cur8(u.steem_username)
            u.delegation_sp = sp if sp > 0 else None
            u.delegation_chain_time = chain_time
            u.delegation_updated_at = now
            updated += 1
        except Exception as e:
            errors.append({"username": u.steem_username, "error": str(e)})

    db.commit()
    return {"updated": updated, "errors": errors}


# ── Settings ───────────────────────────────────────────────────────────────────
@router.get("/settings")
async def get_settings(db: Session = Depends(get_db), _=AdminDep):
    configs = db.query(PlatformConfig).all()
    return {c.key: c.value for c in configs}


@router.put("/settings")
async def update_setting(req: ConfigUpdateRequest, db: Session = Depends(get_db), _=AdminDep):
    set_config(db, req.key, req.value)
    return {"message": "Setting updated", "key": req.key, "value": req.value}
