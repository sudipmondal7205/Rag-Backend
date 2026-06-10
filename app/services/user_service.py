import uuid
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.security import verify_password
from app.exceptions.security_exception import UnauthorizedUserException
from app.exceptions.user_exceptions import UserNotFoundException
from app.models.user import User
from app.repository.user_repo import UserRepository
from app.schema.user import UserLogin, UserResponse


class UserService:

    def __init__(self, session: AsyncSession, user_repo: UserRepository):
        self.repo = user_repo
        self.session = session


    async def get_user_by_id(self, user_id: uuid.UUID):
        user = await self.repo.get_user_by_id(self.session, user_id)
        return UserResponse.model_validate(user)



    async def get_user_by_name(self, name: str):
        return await self.repo.get_user_by_name(self.session, name)



    async def get_all_users(self):
        return await self.repo.get_all_users(self.session)



    async def delete_user(self, user_data: OAuth2PasswordRequestForm):

        existing_user = await self.repo.get_user_by_name(self.session, user_data.username)
        if existing_user is None:
            raise UserNotFoundException(user_data.username)
        
        if not verify_password(user_data.password, existing_user.password):
            raise UnauthorizedUserException(f"Unauthorized user : {user_data.username}")
        
        try:
            await self.repo.delete_user(self.session, existing_user)
            await self.session.commit()

        except Exception as e:
            raise RuntimeError(f"Exception occured : {str(e)}") from e


