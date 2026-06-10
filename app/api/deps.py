from http import HTTPStatus
from typing import Annotated
import uuid
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from psycopg_pool import AsyncConnectionPool
from redis import Redis
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.security import verify_password
from app.db.conv_checkpoint_pool import get_db_pool
from app.db.session import get_session
from app.exceptions.security_exception import CredentialException
from app.models.user import User
from app.repository.conversation_repo import ConversationRepository
from app.repository.document_repo import DocumentRepository
from app.repository.user_repo import UserRepository, userRepository
from app.schema.user import TokenUser
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.email_service import email_service
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.core.llm import get_llm
from app.core.embeddings import get_embedding_model
from supabase import AsyncClient




def get_conversation_repo() -> ConversationRepository:
    return ConversationRepository()

def get_user_repo() -> UserRepository:
    return UserRepository()

def get_document_repo() -> DocumentRepository:
    return DocumentRepository()

def get_supabase_client(request: Request) -> AsyncClient:
    return request.app.state.supabase


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VERSION_PREFIX}/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme)
    ) -> TokenUser:
    try:
        payload = jwt.decode(token=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # id = payload.get('id')
        # name = payload.get('name')
        # user = await userRepository.get_user_by_name(session, name)
        # if user is None:
        #     raise CredentialException(HTTPStatus.UNAUTHORIZED, detail="User not found")
        # if not verify_password(password, user.password):
        #     raise CredentialException(HTTPStatus.UNAUTHORIZED, detail="Password did not match")
        
    except (JWTError) as e:
        raise CredentialException(HTTPStatus.UNAUTHORIZED, str(e))

    return TokenUser.model_validate(payload)





def get_user_service(
        session: AsyncSession = Depends(get_session),
        user_repo: UserRepository = Depends(get_user_repo)
    ):
    return UserService(session, user_repo)


def get_auth_service(
        session: AsyncSession = Depends(get_session),
        redis_client: Redis = Depends(get_redis_client),
        user_repo: UserRepository = Depends(get_user_repo)
    ):
    return AuthService(session, user_repo, redis_client, email_service)


def get_doc_service(
        llm: BaseChatModel = Depends(get_llm),
        embedding: Embeddings = Depends(get_embedding_model),
        session: AsyncSession = Depends(get_session),
        conversation_repo: ConversationRepository = Depends(get_conversation_repo),
        document_repo: DocumentRepository = Depends(get_document_repo),
        supabase_client: AsyncClient = Depends(get_supabase_client)
    ) -> DocumentService:
    return DocumentService(llm, embedding, session, conversation_repo, document_repo, supabase_client)


async def get_conversation_service(
        pool: Annotated[AsyncConnectionPool, Depends(get_db_pool)],
        conversation_repo: Annotated[ConversationRepository, Depends(get_conversation_repo)]
    ) -> ConversationService:
    return ConversationService(pool, conversation_repo)


def get_agent_service(request: Request) -> AgentService:
    return request.app.state.agent_service
