from http import HTTPStatus
import secrets
from redis import Redis
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.exceptions.security_exception import CredentialException, VerificationException
from app.exceptions.user_exceptions import UserAlreadyExistsException, UserNotFoundException
from app.models.user import User
from app.repository.user_repo import UserRepository
from app.schema.user import UserCreate, UserLogin, UserResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.email_service import EmailService



class AuthService():

    def __init__(
            self, session: AsyncSession, 
            user_repository: UserRepository, 
            redis: Redis, 
            email_service: EmailService
        ):
        self.redis_client = redis
        self.user_repo = user_repository
        self.session = session
        self.email_service = email_service


    
    async def authenticate_user(self, user_data: UserLogin) -> str:
        user = await self.user_repo.get_user_by_name(self.session, user_data.name)
        
        if user is None:
            raise UserNotFoundException(user_data.name)
        
        if not verify_password(user_data.password, user.password):
            raise CredentialException(HTTPStatus.UNAUTHORIZED, detail="Password did not match")
            
        return create_access_token(user_data.model_dump())
    


    async def initiate_user_registration(self, user_data: UserCreate):
        
        user = await self.user_repo.get_user_by_name(self.session, user_data.name)
        if user:
            raise UserAlreadyExistsException(user_data.name)

        code = str(secrets.randbelow(1000000)).zfill(6)

        await self.redis_client.setex(f'verification_code:{user_data.email}', settings.REDIS_MEMORY_TIME, code)
        await self.redis_client.setex(f'temp_user:{user_data.email}', settings.REDIS_MEMORY_TIME, user_data.model_dump_json())

        content = f"Verification code: {code}"
        subject = "Verification Email"
        sended = await self.email_service.send_email(user_data.email, content, subject)

        return {"message": "Verification mail sent."}
    


    async def verify_user_email(self, email: str, code_from_user: str):

        stored_code = await self.redis_client.get(f'verification_code:{email}')

        if stored_code is None or stored_code != code_from_user:
            raise VerificationException("Verification failed!!!")
        
        user_data = await self.redis_client.get(f'temp_user:{email}')
        if user_data is None:
            raise VerificationException("Verification failed!!!")
        
        user = User.model_validate_json(user_data)
        user.password = hash_password(user.password)
        created_user = await self.user_repo.create_user(self.session, user)

        return UserResponse.model_validate(created_user)
    
        