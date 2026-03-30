from fastapi import APIRouter, Depends

from app.models import User
from app.core.utils import get_user

router = APIRouter(tags=["account"])


@router.get(f"/mine", response_model=User)
async def mine(current_user: User = Depends(get_user)):
    return current_user
