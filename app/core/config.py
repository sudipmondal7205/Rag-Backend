from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings) :

    BACKEND_URL: str

    DB: str = "postgresql"
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    ENV: str
    DEBUG: bool

    API_VERSION: str

    COHERE_API_KEY: str


    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 2000


    @property
    def CONV_DB_URL(self) -> str:
        return (
            f"{self.DB}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    

    @property
    def USER_DB_URL(self) -> str:
        return (
            f"{self.DB}+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    
    PINECONE_DB_API_KEY: str
    PINECONE_INDEX_NAME: str
    EMBEDDING_DIMENSION: int


    REDIS_URI: str
    REDIS_MEMORY_TIME: int = 3600


    GMAIL_REFRESH_TOKEN: str
    GMAIL_CLIENT_ID: str
    GMAIL_CLIENT_SECRET: str
    GMAIL_SENDER: str


    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    DEFAULT_PROFILE_PICTURE_URL: str = "https://mdresuykkhrimmplcwum.supabase.co/storage/v1/object/public/avatars/default/default-profile-picture.jpg"
    

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    

    GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"


    @property
    def REDIRECT_URI(self) -> str:
        return f"{self.BACKEND_URL}/api/v1/auth/google/callback"
    

    @property
    def API_VERSION_PREFIX(self) -> str:
        return (
            f"/api/{self.API_VERSION}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"




settings = Settings()