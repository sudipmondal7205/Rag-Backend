from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_user_service
from app.models.user import User
from app.services.user_service import UserService



router = APIRouter(prefix="/user", tags=["User"])



@router.get("/get-user/all")
async def get_all_users(
        user_service: UserService = Depends(get_user_service)
    ):
    return await user_service.get_all_users()


@router.get("/get-user/{user_id}")
async def get_user_by_id(
        user_id: int,
        user_service: UserService = Depends(get_user_service)
    ):
    return await user_service.get_user_by_id(user_id)


@router.delete("/delete-user")
async def delete_user(
        user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service)
    ):
    return await user_service.delete_user(user)