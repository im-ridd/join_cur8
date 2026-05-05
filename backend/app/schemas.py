from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Auth
class GoogleCallbackData(BaseModel):
    code: str
    state: Optional[str] = None

class EmailRegisterRequest(BaseModel):
    email: EmailStr
    referrer: Optional[str] = None

class EmailVerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str

class SendOTPRequest(BaseModel):
    phone: str
    referrer: Optional[str] = None

class VerifyOTPRequest(BaseModel):
    phone: str
    code: str


# Steem
class CheckUsernameResponse(BaseModel):
    available: bool
    username: str

class CreateAccountRequest(BaseModel):
    username: str
    referrer: Optional[str] = None

class AccountKeysResponse(BaseModel):
    username: str
    master_password: str
    owner_key: str
    active_key: str
    posting_key: str
    memo_key: str


# Referral
class ReferralLookupResponse(BaseModel):
    steem_username: str
    referrer: Optional[str]
    beneficiary_pct: Optional[float]


# Admin
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class ConfigUpdateRequest(BaseModel):
    key: str
    value: str

class ReferrerConfigUpdate(BaseModel):
    beneficiary_pct: float
    notes: Optional[str] = None



class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Steem
class CheckUsernameResponse(BaseModel):
    available: bool
    username: str

class CreateAccountRequest(BaseModel):
    username: str
    referrer: Optional[str] = None

class AccountKeysResponse(BaseModel):
    username: str
    master_password: str
    owner_key: str
    active_key: str
    posting_key: str
    memo_key: str


# Referral
class ReferralLookupResponse(BaseModel):
    steem_username: str
    referrer: Optional[str]


# Admin
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class ConfigUpdateRequest(BaseModel):
    key: str
    value: str

class RewardDistributeRequest(BaseModel):
    reward_ids: list[str]


# User info
class UserInfo(BaseModel):
    id: str
    steem_username: Optional[str]
    auth_provider: str
    referrer_steem: Optional[str]
    account_created: bool
    created_at: datetime
