from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models import User, UserCreate, Token
from app.core.utils import get_password_hash, verify_password, create_token, get_user

from app.routers.account import router as account_router

router = APIRouter(tags=["auth"])
router.include_router(account_router, prefix="/account")


@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_session)):
    result = await db.exec(select(User).where(User.username == user.username))
    existing_user = result.first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password)

    db.add(new_user)
    await db.commit()

    access_token = create_token({"sub": new_user.username, "version": new_user.token_version})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(user: UserCreate, db: AsyncSession = Depends(get_session)):
    result = await db.exec(select(User).where(User.username == user.username))
    existing_user = result.first()

    if not existing_user or not verify_password(
        user.password, existing_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_token({"sub": existing_user.username, "version": existing_user.token_version})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/validate")
async def validate(
    user: User = Depends(get_user), db: AsyncSession = Depends(get_session)
):
    return {"username": user.username}
