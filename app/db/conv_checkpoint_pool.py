from app.core.config import settings
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row


pool = AsyncConnectionPool(
    conninfo=settings.CONV_DB_URL,
    max_size=20,
    open=False,
    kwargs={"autocommit": True, "row_factory": dict_row}
)
