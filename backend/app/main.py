import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()  # loads backend/.env for local development

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .database import init_db
from .routers import auth, steem, referral, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield



app = FastAPI(title="join.cur8.fun", version="1.0.0", lifespan=lifespan)

# Session middleware required for OAuth state
app.add_middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET_KEY", "change-me"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "https://join.cur8.fun").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(steem.router)
app.include_router(referral.router)
app.include_router(admin.router)

# Serve static admin files
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Serve admin panel frontend (same-origin → no cookie/CORS issues)
_admin_ui_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "admin")
_admin_ui_dir = os.path.normpath(_admin_ui_dir)
if os.path.exists(_admin_ui_dir):
    app.mount("/admin-ui", StaticFiles(directory=_admin_ui_dir, html=True), name="admin-ui")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "join.cur8.fun"}

@app.get("/admin", include_in_schema=False)
async def admin_redirect():
    return RedirectResponse(url="/admin/")
