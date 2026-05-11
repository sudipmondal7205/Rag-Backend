from fastapi import APIRouter, Depends
from pydantic import EmailStr
from app.api.deps import get_auth_service
from app.schema.user import UserCreate, UserLogin
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth")


@router.post("/login")
async def login_user(
        user_data: UserLogin,
        auth_service: AuthService = Depends(get_auth_service)
    ):
    return await auth_service.authenticate_user(user_data)


@router.post("/create-user/register")
async def register(
        user_data: UserCreate,
        auth_service: AuthService = Depends(get_auth_service)    
    ):
    return await auth_service.initiate_user_registration(user_data)


@router.post("/create-user/verify")
async def verify(
        email: EmailStr,
        verification_code: str,
        auth_service: AuthService = Depends(get_auth_service)
    ):
    return await auth_service.verify_user_email(email, verification_code)