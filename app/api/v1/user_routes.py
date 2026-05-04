from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.exceptions.user_exceptions import UserAlreadyExistsException
from app.schema.user import UserCreate
from app.services.user_service import userService


router = APIRouter(prefix="/user", tags=["User"])


@router.post("/")
async def create_user(
        user_data: UserCreate,
        session: AsyncSession = Depends(get_session)
    ):
    
    return await userService.register_user(user_data, session)
    



@router.get("/all")
async def get_all_users(session: AsyncSession = Depends(get_session)):
    return await userService.get_all_users(session)




