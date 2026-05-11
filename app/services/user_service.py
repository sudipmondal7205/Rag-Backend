import uuid
from sqlmodel.ext.asyncio.session import AsyncSession
from app.exceptions.user_exceptions import UserNotFoundException
from app.models.user import User
from app.repository.user_repo import UserRepository
from app.schema.user import UserLogin


class UserService:

    def __init__(self, session: AsyncSession, user_repo: UserRepository):
        self.repo = user_repo
        self.session = session


    async def get_user_by_id(self, user_id: uuid.UUID):
        result = await self.repo.get_user_by_id(self.session, user_id)
        return result



    async def get_user_by_name(self, name: str):
        return await self.repo.get_user_by_name(self.session, name)



    async def get_all_users(self):
        return await self.repo.get_all_users(self.session)


    async def delete_user(self, user: User):
        existing_user = await self.repo.get_user_by_id(self.session, user.id)
        if existing_user is None:
            raise UserNotFoundException(user.name)
        
        try:
            await self.repo.delete_user(self.session, existing_user)
            await self.session.commit()
        except Exception as e:
            return str(e)


