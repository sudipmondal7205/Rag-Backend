from http import HTTPStatus
import uuid
from fastapi import HTTPException, UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession
from app.exceptions.file_exception import FileException
from app.exceptions.user_exceptions import UserNotFoundException
from app.repository.conversation_repo import ConversationRepository
from app.repository.user_repo import UserRepository
from app.schema.user import TokenUser, UserResponse
from supabase import AsyncClient
from app.services.conversation_service import ConversationService
from app.core.config import settings

class UserService:

    def __init__(self, session: AsyncSession,
        supabase_client: AsyncClient,
        user_repo: UserRepository,
        conv_service: ConversationService,
        conversation_repo: ConversationRepository 
    ):
        self._user_repo = user_repo
        self._session = session
        self._supabase_client = supabase_client
        self._conversation_service = conv_service
        self._conversation_repo = conversation_repo

    async def get_user_by_id(self, user_id: uuid.UUID):
        user = await self._user_repo.get_user_by_id(self._session, user_id)
        return UserResponse.model_validate(user)



    async def get_user_by_email(self, email: str):
        return await self._user_repo.get_user_by_email(self._session, email)



    async def update_profile_picture(self, file: UploadFile, user_id: uuid.UUID):
        allowed_extensions = ["image/jpeg", "image/jpg", "image/png", "image/webp"]

        if file.content_type not in allowed_extensions:
            raise FileException(
                status_code=HTTPStatus.BAD_REQUEST, 
                detail="Invalid file type. Only JPEG, PNG, and WebP are allowed."    
            )
        
        file_bytes = await file.read()
        file_extension = file.filename.split('.')[-1]
        storage_path = f"profile/{user_id}/avatar.{file_extension}"

        try:
            await self._supabase_client.storage.from_("avatars").upload(
                file=file_bytes,
                path=storage_path,
                file_options={"content-type": file.content_type, "upsert": "true"}
            )
            public_url_response = await self._supabase_client.storage.from_("avatars").get_public_url(storage_path)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save profile picture to cloud storage: {str(e)}")

        user = await self._user_repo.get_user_by_id(self._session, user_id)
        user.profile_pic = public_url_response
        await self._user_repo.save_user(self._session, user)

        return UserResponse.model_validate(user)



    async def get_all_users(self):
        return await self._user_repo.get_all_users(self._session)


    
    async def delete_user(self, current_user: TokenUser):
        existing_user = await self._user_repo.get_user_by_id(self._session, current_user.id)
        if existing_user is None:
            raise UserNotFoundException(current_user.email)
        
        try:
            conversations = await self._conversation_repo.get_conversations_by_user(self._session, existing_user.id)
            for conversation in conversations:
                await self._conversation_service.delete_conversation_assets(conversation)

            if existing_user.profile_pic.startswith(f"{settings.SUPABASE_URL}/storage/v1/object/public/avatars/profile", 0):
                try:
                    profile_pic_path = existing_user.profile_pic.removeprefix(f"{settings.SUPABASE_URL}/storage/v1/object/public/avatars/")
                    await self._supabase_client.storage.from_('avatars').remove([profile_pic_path])
                except Exception:
                    pass

            await self._user_repo.delete_user(self._session, existing_user)
            await self._session.commit()

        except Exception as e:
            await self._session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
                detail=f"Exception occured : {str(e)}"
            )


