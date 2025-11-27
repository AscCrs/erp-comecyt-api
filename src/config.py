from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

# --- CORRECCIÓN DE RUTA (ESTRUCTURA PLANA) ---
# Obtenemos la ruta de LA CARPETA donde está este archivo (config.py).
# Como tu .env está al mismo nivel, lo buscamos ahí directamente.
current_dir = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.join(current_dir, ".env")

class Settings(BaseSettings):
    """
    Configuración global.
    Busca el archivo .env en la misma carpeta que config.py
    """

    # --- 1. BASE DE DATOS ---
    DATABASE_URL: str

    # --- 2. SEGURIDAD ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- 3. ALMACENAMIENTO ---
    AZURE_CONNECTION_STRING: str
    AZURE_CONTAINER_NAME: str

    # Configuración Pydantic V2
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,     # Ruta absoluta calculada
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"              # Ignora variables extra del .env
    )

@lru_cache()
def get_settings() -> Settings:
    # Imprimimos para depurar si sigue fallando (verás esto en la consola al arrancar)
    # print(f"Cargando configuración desde: {ENV_FILE_PATH}")
    return Settings()