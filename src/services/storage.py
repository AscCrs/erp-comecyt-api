from azure.storage.blob import BlobServiceClient
from fastapi import UploadFile, HTTPException
import uuid
import os
from ..config import get_settings

settings = get_settings()

async def upload_image_to_azure(file: UploadFile) -> str:
    """
    Sube un archivo a Azure Blob Storage y retorna la URL pública.
    """
    try:
        # 1. Validar extensión (básico)
        filename = file.filename
        ext = os.path.splitext(filename)[1]
        if ext.lower() not in [".jpg", ".jpeg", ".png", ".mp4"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no permitido")

        # 2. Generar nombre único para evitar colisiones
        unique_filename = f"{uuid.uuid4()}{ext}"

        # 3. Conectar al cliente
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(
            container=settings.AZURE_CONTAINER_NAME, 
            blob=unique_filename
        )

        # 4. Subir el archivo
        # Importante: file.file es el objeto binario en FastAPI
        blob_client.upload_blob(file.file, overwrite=True)

        # 5. Construir la URL
        blob_url = blob_client.url
        return blob_url

    except Exception as e:
        print(f"Error subiendo a Azure: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar la imagen en el servidor")