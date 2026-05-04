import re
from typing import Coroutine

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from app.schema.user import UserCreate



class UserRepository:

    def __init__(self):
        pass

    async def get_user_by_id(self, session: AsyncSession, user_id):
        return await session.get(User, user_id)


    async def create_user(self, session: AsyncSession, user: User):
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


    async def get_all_users(self, session: AsyncSession):
        statement = select(User)
        result = await session.exec(statement)
        return result.all()


    async def get_user_by_email(self, session: AsyncSession, email: str):
        statement = (
            select(User).where(User.email == email)
        )
        result = await session.exec(statement)
        return result.first()
    

    async def get_user_by_name(self, session: AsyncSession, name: str):
        statement = (
            select(User).where(User.name == name)
        )
        result = await session.exec(statement)
        return result.first()
    


userRepository = UserRepository()

