from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación, cargada desde variables de entorno o .env."""

    app_name: str = "Finanzas App"
    debug: bool = True
    database_url: str = "sqlite:///./finanzas.db"
    secret_key: str = "cambia-esta-clave-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # Un movimiento igual o mayor a este valor genera una alerta
    large_transaction_amount: Decimal = Decimal("1000000")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
