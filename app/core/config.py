from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación, cargada desde variables de entorno o .env."""

    app_name: str = "Finanzas App"
    debug: bool = True
    database_url: str = "sqlite:///./finanzas.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
