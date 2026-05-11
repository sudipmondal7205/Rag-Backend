from http import HTTPStatus
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from redis import Redis
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.security import verify_password
from app.db.session import get_session
from app.exceptions.security_exception import CredentialException
from app.models.user import User
from app.repository.user_repo import userRepository
from app.services.email_service import email_service
from app.services.auth_service import AuthService
from app.services.user_service import UserService



oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VERSION_PREFIX}/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session)
) -> User:
    
    try:
        payload = jwt.decode(token=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        print(payload)
        name = payload.get('name')
        password = payload.get('password')

        user = await userRepository.get_user_by_name(session, name)
        if user is None:
            raise CredentialException(HTTPStatus.UNAUTHORIZED, detail="User not found")
        
        if not verify_password(password, user.password):
            raise CredentialException(HTTPStatus.UNAUTHORIZED, detail="Password did not match")
        
    except (JWTError, ExpiredSignatureError) as e:
        raise CredentialException(HTTPStatus.UNAUTHORIZED, str(e))

    return user



async def get_user_service(
        session: AsyncSession = Depends(get_session)
    ):
    return UserService(session, userRepository)



async def get_auth_service(
        session: AsyncSession = Depends(get_session),
        redis: Redis = Depends(get_redis_client),
    ):
    return AuthService(session, userRepository, redis, email_service)