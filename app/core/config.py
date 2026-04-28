from pydantic_settings import BaseSettings


class Settings(BaseSettings) :

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    ENV: str
    DEBUG: bool

    API_VERSION: str
    API_PREFIX: str

    CONV_CHECKPOINT_DB_URL: str

    COHERE_API_KEY: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    
    @property
    def API_VERSION_PREFIX(self) -> str:
        return (
            f"{self.API_PREFIX}/{self.API_VERSION}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()