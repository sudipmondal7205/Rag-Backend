from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_user_service
from app.models.user import User
from app.schema.user import UserResponse
from app.services.user_service import UserService



router = APIRouter(prefix="/user", tags=["user"])



@router.get("/get-user/all")
async def get_all_users(
        user_service: UserService = Depends(get_user_service)
    ):
    return await user_service.get_all_users()


@router.get("/get-user")
async def get_user(
        user: User = Depends(get_current_user),
    ):
    return UserResponse.model_validate(user)


@router.delete("/delete-user")
async def delete_user(
        user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service)
    ):
    return await user_service.delete_user(user)