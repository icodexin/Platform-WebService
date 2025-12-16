from urllib.parse import quote
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Collect Platform"
    ENCRYPTION_ALGORITHM: str = "HS256"
    TOKEN_KEY: str = "your_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "platform"
    MYSQL_USER: str = "admin"
    MYSQL_PASSWORD: str = "password"

    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    @property
    def DATABASE_URL(self) -> str:
        username = quote(self.MYSQL_USER, safe='')
        password = quote(self.MYSQL_PASSWORD, safe='')
        return (
            f"mysql+asyncmy://{username}:{password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(env_prefix='WEBSERVICE_')


settings = Settings()
