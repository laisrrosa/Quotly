#Para validação de variáveis de ambiente
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quotly API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./quotly.db"

    #Config de Criptografia e auth (JWT)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    #configuração do pydantic para apontar para o arquivo de env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

#instancia da classe para que todo projeto importe 'settings' pronto
settings = Settings()