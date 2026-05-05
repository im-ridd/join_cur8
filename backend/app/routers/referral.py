from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db, get_config
from ..models import JoinUser, ReferrerConfig

router = APIRouter(prefix="/api/referral", tags=["referral"])


@router.get("/lookup")
async def lookup_referrer(steem: str, db: Session = Depends(get_db)):
    """
    Used by games.cur8.fun to get the referrer and beneficiary % for a Steem account.
    No authentication required — accessible only within cur8 network.
    """
    steem = steem.lower().strip()
    user = db.query(JoinUser).filter_by(steem_username=steem).first()
    referrer = user.referrer_steem if user else None

    beneficiary_pct = None
    if referrer:
        cfg = db.query(ReferrerConfig).filter_by(steem_username=referrer).first()
        if cfg:
            beneficiary_pct = cfg.beneficiary_pct
        else:
            beneficiary_pct = float(get_config(db, "default_beneficiary_pct", "5.0"))

    return {
        "steem_username": steem,
        "referrer": referrer,
        "beneficiary_pct": beneficiary_pct,
    }


@router.get("/stats/{referrer_steem}")
async def referrer_stats(referrer_steem: str, db: Session = Depends(get_db)):
    """Public stats for a referrer (how many users they've brought in)."""
    count = db.query(JoinUser).filter_by(referrer_steem=referrer_steem).count()
    referred = db.query(JoinUser).filter_by(referrer_steem=referrer_steem).all()
    return {
        "referrer": referrer_steem,
        "total_referred": count,
        "referred_users": [u.steem_username for u in referred if u.steem_username],
    }

