from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions.security_exception import CredentialException, VerificationException
from app.exceptions.user_exceptions import UserAlreadyExistsException, UserNotFoundException
from app.repository.user_repo import UserRepository
from app.schema.user import UserCreate, UserResponse, UserVerifySchema
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.email_service import EmailService
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.user import User
from http import HTTPStatus
from redis import Redis
import secrets
import httpx
import jwt



class AuthService():

    def __init__(
            self, session: AsyncSession, 
            user_repository: UserRepository, 
            redis: Redis,
            email_service: EmailService
        ):
        self._redis_client = redis
        self._user_repo = user_repository
        self._session = session
        self._email_service = email_service


    
    async def authenticate_user(self, user_data: OAuth2PasswordRequestForm) -> str:
        user = await self._user_repo.get_user_by_email(self._session, user_data.username)
        
        if user is None:
            raise UserNotFoundException(user_data.username)
        
        if not verify_password(user_data.password, user.password):
            raise CredentialException(HTTPStatus.UNAUTHORIZED, detail="Password did not match")
        
        return create_access_token({
            'id': str(user.id),
            'email': user.email
        })
    


    async def initiate_user_registration(self, user_data: UserCreate):
        
        user = await self._user_repo.get_user_by_email(self._session, user_data.email)
        if user:
            raise UserAlreadyExistsException(user_data.email)

        code = str(secrets.randbelow(1000000)).zfill(6)
        print("OTP: ", code)
        await self._redis_client.setex(f'verification_code:{user_data.email}', settings.REDIS_MEMORY_TIME, code)
        await self._redis_client.setex(f'temp_user:{user_data.email}', settings.REDIS_MEMORY_TIME, user_data.model_dump_json())

        sended = await self._email_service.send_otp_email(user_data.email, code)
        if not sended:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
                detail=f"Can't send verification mail to {user_data.email}"
            )
        return {"message": f"Verification mail sent to {user_data.email}."}
    


    async def verify_user_email(self, data: UserVerifySchema):

        stored_code = await self._redis_client.get(f'verification_code:{data.email}')

        if stored_code is None or stored_code != data.verification_code:
            raise VerificationException(detail="Invalid OTP!!!")
        
        user_data = await self._redis_client.get(f'temp_user:{data.email}')
        if user_data is None:
            raise VerificationException(detail="Verificatio n failed!!!")
        
        existing_user = await self._user_repo.get_user_by_email(self._session, data.email)
        if existing_user:
            raise VerificationException(status_code=HTTPStatus.BAD_REQUEST, detail=f"User with email {data.email} already verified.")
        
        user = User.model_validate_json(user_data)
        user.password = hash_password(user.password)
        user.profile_pic = settings.DEFAULT_PROFILE_PICTURE_URL
        created_user = await self._user_repo.save_user(self._session, user)

        return UserResponse.model_validate(created_user)
    
        

    def google_login(self):
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account"
        }

        url_request = httpx.URL(settings.GOOGLE_AUTH_URL, params=params)
        return RedirectResponse(url=url_request)



    async def google_callback(self, code: str):
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                settings.GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.REDIRECT_URI
                },
            )

        if token_response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange token with Google.")
        
        token_data = token_response.json()
        id_token = token_data.get('id_token')

        try:
            user_info = jwt.decode(id_token, options={"verify_signature": False})
            email = user_info.get("email")
            google_sub_id = user_info.get("sub")
            name = user_info.get('name')
            picture_url = user_info.get("picture")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange token with Google.")
        
        user = await self._user_repo.get_user_by_email(self._session, email)
        if not user:
            user = User(
                email=email,
                password="OAUTH_NATIVE_USER",
                full_name=name,
                profile_pic=picture_url
            )
            user = await self._user_repo.save_user(self._session, user)

        else:
            if user.profile_pic != picture_url:
                user.profile_pic = picture_url
                await self._user_repo.save_user(self._session, user)
        
        user_data = {
            "id": str(user.id),
            "email": email
        }
        access_token = create_access_token(user_data)

        redirect_url = f"http://localhost:3000/?token={access_token}"
        return RedirectResponse(url=redirect_url)
