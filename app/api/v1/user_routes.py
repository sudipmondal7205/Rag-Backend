from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_current_user, get_user_service
from app.schema.user import TokenUser, UserResponse
from app.services.user_service import UserService



router = APIRouter(prefix="/user", tags=["user"])



@router.get("/get-user/all")
async def get_all_users(
        user_service: Annotated[UserService, Depends(get_user_service)]
    ):
    return await user_service.get_all_users()


@router.get("/get-user", response_model=UserResponse)
async def get_user(
        current_user: Annotated[TokenUser, Depends(get_current_user)],
        user_service: Annotated[UserService, Depends(get_user_service)]
    ):
    return await user_service.get_user_by_id(current_user.id)


@router.delete("/delete-user")
async def delete_user(
        user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        user_service: Annotated[UserService, Depends(get_user_service)]
    ):
    try:
        await user_service.delete_user(user_data)
        return JSONResponse(
            content=f"User : {user_data.username} deleted successfully.",
            status_code=HTTPStatus.OK
        )
    except Exception as e:
        return JSONResponse(
            content=f"Error: {str(e)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )