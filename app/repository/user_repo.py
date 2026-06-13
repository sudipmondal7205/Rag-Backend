import uuid
from pydantic import EmailStr
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User



class UserRepository:

    async def get_user_by_id(self, session: AsyncSession, user_id: uuid.UUID):
        return await session.get(User, user_id)


    async def save_user(self, session: AsyncSession, user: User):
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    

    async def get_all_users(self, session: AsyncSession):
        statement = select(User)
        result = await session.exec(statement)
        return result.all()


    async def get_user_by_email(self, session: AsyncSession, email: EmailStr) -> User:
        statement = (
            select(User).where(User.email == email)
        )
        result = await session.exec(statement)
        return result.first()
    
    

    async def delete_user(self, session: AsyncSession, user: User):
        await session.delete(user)
        await session.flush()


userRepository = UserRepository()

