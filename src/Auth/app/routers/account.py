from fastapi import APIRouter, Depends

from app.models import User
from app.core.utils import TokenValidator

router = APIRouter(tags=["account"])


@router.get(f"/mine", response_model=User)
async def mine(current_user: User = Depends(TokenValidator("access"))):
    return current_user
