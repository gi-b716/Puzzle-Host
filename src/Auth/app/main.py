__VERSION__ = "0.1.0"

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import auth_router, account_router
from app.core.utils import JWKS


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Puzzhle Host / Auth",
    description="去中心化 Puzzlehunt 平台的全局身份认证中心",
    version=__VERSION__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(account_router, prefix="/account")


@app.get("/.well-known/jwks.json", tags=["public"])
async def get_jwks():
    return JWKS


@app.get("/")
async def root():
    return {"status": "ok", "version": __VERSION__}
