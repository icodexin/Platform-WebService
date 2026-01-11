from urllib.parse import quote
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Collect Platform"
    ENCRYPTION_ALGORITHM: str = "HS256"
    TOKEN_KEY: str = "your_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "platform"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "password"

    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    SYS_ADMIN_USER: str = "admin"
    SYS_ADMIN_INIT_PWD: str = "admin123"

    @property
    def DATABASE_URL(self) -> str:
        username = quote(self.POSTGRES_USER, safe='')
        password = quote(self.POSTGRES_PASSWORD, safe='')
        return (
            f"postgresql+asyncpg://{username}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def RABBITMQ_URL(self) -> str:
        username = quote(self.RABBITMQ_USER, safe='')
        password = quote(self.RABBITMQ_PASSWORD, safe='')
        return f"amqp://{username}:{password}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding='utf-8'
    )


settings = Settings()
