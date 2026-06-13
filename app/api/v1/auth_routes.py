from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_auth_service
from app.schema.user import UserCreate, UserVerifySchema
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=['auth'])


@router.post("/login")
async def login_user(
        user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
    ):
    access_token = await auth_service.authenticate_user(user_data)

    return {
        'access_token': access_token,
        'token_type': 'bearer'
    }


@router.post("/create-user/register")
async def register(
        user_data: UserCreate,
        auth_service: Annotated[AuthService, Depends(get_auth_service) ]   
    ):
    return await auth_service.initiate_user_registration(user_data)


@router.post("/create-user/verify")
async def verify(
        data: UserVerifySchema,
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
    ):
    return await auth_service.verify_user_email(data)



@router.get("/google/login")
async def get_google_login_url(
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
    ):
    return auth_service.google_login()
    

@router.get("/google/callback")
async def google_callback(
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
        code: Annotated[str, Query(...)]
    ):
    return await auth_service.google_callback(code)
    
    