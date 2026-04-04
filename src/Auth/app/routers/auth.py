from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models import User, UserAuth, ResetPassword, Token
from app.core.utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    TokenValidator,
)

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user: UserAuth, db: AsyncSession = Depends(get_session)):
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

    access_token = create_access_token(new_user)
    refresh_token = create_refresh_token(new_user)
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/login", response_model=Token)
async def login(user: UserAuth, db: AsyncSession = Depends(get_session)):
    result = await db.exec(select(User).where(User.username == user.username))
    existing_user = result.first()

    if not existing_user or not verify_password(
        user.password, existing_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(existing_user)
    refresh_token = create_refresh_token(existing_user)
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/reset_password", response_model=Token)
async def reset_password(
    user: ResetPassword,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(TokenValidator("access")),
):
    if not verify_password(user.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password",
        )

    current_user.password_hash = get_password_hash(user.new_password)
    current_user.token_version += 1  # 增加 token_version 以使旧 Token 失效
    db.add(current_user)
    await db.commit()

    access_token = create_access_token(current_user)
    refresh_token = create_refresh_token(current_user)
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_endpoint(current_user: User = Depends(TokenValidator("refresh"))):
    access_token = create_access_token(current_user)
    refresh_token = create_refresh_token(current_user)
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_tokens(
    current_user: User = Depends(TokenValidator("access")),
    db: AsyncSession = Depends(get_session),
):
    current_user.token_version += 1
    db.add(current_user)
    await db.commit()
