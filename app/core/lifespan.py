from contextlib import asynccontextmanager
from app.core.embeddings import get_embedding_model
from app.core.llm import get_llm
from app.db.init_db import init_db
from app.db.conv_checkpoint_pool import pool
from fastapi import FastAPI
from app.repository.conversation_repo import ConversationRepository
from app.services.agent_service import AgentService
from supabase import acreate_client
from app.core.config import settings



@asynccontextmanager
async def lifespan(app: FastAPI):

    await pool.open()
    await init_db()


    app.state.supabase = await acreate_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_ANON_KEY
    )


    llm = get_llm()
    embedding_model = get_embedding_model()
    conversation_repo = ConversationRepository()
    app.state.agent_service = AgentService(llm, embedding_model, pool, conversation_repo)

    yield

    await pool.close()