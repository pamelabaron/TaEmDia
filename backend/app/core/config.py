"""Configuração central da aplicação, lida a partir de variáveis de ambiente (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco
    DATABASE_URL: str = "postgresql+psycopg://taemdia:troque_esta_senha@db:5432/taemdia"

    # JWT
    JWT_SECRET: str = "dev-secret-troque-em-producao"
    JWT_EXPIRE_MINUTES: int = 1440

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Endereço do frontend (para onde o login redireciona com o token)
    FRONTEND_URL: str = "http://localhost:4200"

    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""


settings = Settings()
