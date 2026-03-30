from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models import User, UserResetPassword, Token
from app.core.utils import get_password_hash, verify_password, create_token, get_user

router = APIRouter(tags=["auth/account"])


@router.post("/reset-password", response_model=Token)
async def reset_password(
    user: UserResetPassword,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_user),
):
    if not verify_password(user.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid old password",
        )

    current_user.password_hash = get_password_hash(user.new_password)
    current_user.token_version += 1  # 增加 token_version 以使旧 Token 失效
    db.add(current_user)
    await db.commit()

    access_token = create_token({"sub": current_user.username})
    return Token(access_token=access_token, token_type="bearer")
