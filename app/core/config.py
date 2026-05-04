from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings) :

    DB: str = Field(default="postgresql")
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
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 240

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
    
    @property
    def API_VERSION_PREFIX(self) -> str:
        return (
            f"/api/{self.API_VERSION}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()