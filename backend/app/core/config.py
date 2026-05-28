from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://smarthome:smarthome123@localhost:5432/smarthome"
    redis_url: str = "redis://localhost:6379"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = "backend"
    mqtt_password: str = "backend_secret"
    secret_key: str = "dev-secret-key"

    class Config:
        env_file = ".env"


settings = Settings()
