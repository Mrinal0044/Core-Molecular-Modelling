import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Quantum PharmX Backend"
    DEBUG: bool = False
    
    # Security
    JWT_SECRET_KEY: str = "supersecretkey_replace_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/pharmx_db"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # Converts postgresql:// or postgres:// to postgresql+asyncpg://
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # Celery & Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    # Limits & Allowed Formats
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_PROTEIN_EXTENSIONS: List[str] = [".pdb"]
    ALLOWED_LIGAND_EXTENSIONS: List[str] = [".sdf", ".mol2", ".pdbqt"]

    # AutoDock Vina Config
    VINA_EXECUTABLE: str = "vina"  # Can be path to vina executable
    OBABEL_EXECUTABLE: str = "obabel"  # Can be path to obabel executable

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
