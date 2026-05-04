from sqlmodel.ext.asyncio.session import AsyncSession
from app.exceptions.user_exceptions import UserAlreadyExistsException
from app.models.user import User
from app.repository.user_repo import userRepository
from app.schema.user import UserCreate, UserResponse
from app.core.security import hash_password


class UserService:

    def __init__(self):
        self.repo = userRepository
    

    async def register_user(self, user_data: UserCreate, session: AsyncSession):

        existing_user = await self.repo.get_user_by_name(session, user_data.name)
        if existing_user:
            raise UserAlreadyExistsException(user_data.name)
        
        user_data.password = hash_password(user_data.password)

        user = User.model_validate(user_data)
        created_user = await self.repo.create_user(session, user)

        return UserResponse.model_validate(created_user)


    async def get_all_users(self, session: AsyncSession):
        return await self.repo.get_all_users(session)


userService = UserService()