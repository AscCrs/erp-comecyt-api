from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from .. import database, schemas, models

from ..services.storage import upload_image_to_azure

router = APIRouter(
    prefix="/public",
    tags=["Ciudadanía (Acceso Libre)"]
)

# --- 1. CATÁLOGOS ---

@router.get("/zonas", response_model=List[schemas.ZonaResponse])
def get_zonas(db: Session = Depends(database.get_db)):
    """
    Obtiene la lista de municipios (Zonas) disponibles.
    Uso: Llenar el Dropdown en la App Flutter.
    """
    zonas = db.query(models.Zona).all()
    return zonas

# --- GESTIÓN DE MULTIMEDIA ---

@router.post("/evidence/upload", status_code=status.HTTP_201_CREATED)
async def upload_evidence_file(file: UploadFile = File(...)):
    """
    Endpoint dedicado para subir imágenes/videos a Azure Blob Storage.
    
    Flujo para Flutter:
    1. El usuario toma la foto.
    2. Flutter envía la foto a este endpoint.
    3. Este endpoint devuelve: {"url": "https://azure..."}
    4. Flutter toma esa URL y la envía al endpoint POST /tickets en el campo 'evidence_url'.
    """
    # Validación básica de tipo de archivo
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "video/mp4"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de archivo no permitido. Tipos válidos: {allowed_types}"
        )
    
    # Llamada al servicio de Azure (definido en app/services/storage.py)
    try:
        url = await upload_image_to_azure(file)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. GESTIÓN DE REPORTES (TICKETS) ---

@router.post("/tickets", response_model=schemas.TicketResponse, status_code=status.HTTP_201_CREATED)
def create_public_ticket(
    ticket: schemas.TicketCreatePublic, 
    db: Session = Depends(database.get_db)
):
    """
    Crea un nuevo reporte ciudadano.
    
    - **id_zona_ticket**: ID del municipio seleccionado.
    - **id_usuario_reporte_ticket**: UUID generado en el dispositivo móvil.
    - **evidence_base64**: (Opcional) Si envías la imagen aquí en base64, 
      deberías procesarla antes. *Nota: Para Hackathon, se recomienda usar el endpoint 
      Multipart del main.py si subes archivos reales, o este si solo envías JSON.*
    """
    
    # Validar que la zona exista
    zona = db.query(models.Zona).filter(models.Zona.id_zona == ticket.id_zona_ticket).first()
    if not zona:
        raise HTTPException(status_code=404, detail="La zona seleccionada no existe")

    # Crear el objeto Ticket
    # Por defecto, asignamos a una Organización "Buzón General" (ej. ID 1) 
    # o dejamos que el router de backend lo asigne después.
    # Aquí asumimos ID_ORGANIZACION = 1 como 'Ventanilla Única'.
    
    new_ticket = models.Ticket(
        id_usuario_reporte_ticket=ticket.id_usuario_reporte_ticket,
        descripcion_ticket=ticket.descripcion_ticket,
        des_hechos_lugar_ticket=ticket.des_hechos_lugar_ticket,
        tipo_incidente_ticket=ticket.tipo_incidente_ticket,
        id_zona_ticket=ticket.id_zona_ticket,
        ubicacion_lat_ticket=ticket.ubicacion_lat_ticket,
        ubicacion_lon_ticket=ticket.ubicacion_lon_ticket,
        id_organizacion_ticket=1, # ID temporal hasta que se asigne
        estado_ticket=models.EstadoTicket.RECIBIDO
    )
    
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    return new_ticket

@router.get("/tickets/status/{user_uuid}", response_model=List[schemas.TicketResponse])
def get_my_tickets_status(user_uuid: str, db: Session = Depends(database.get_db)):
    """
    Permite al ciudadano consultar el historial de SUS reportes.
    Filtra por el UUID del dispositivo.
    """
    tickets = db.query(models.Ticket).filter(
        models.Ticket.id_usuario_reporte_ticket == user_uuid
    ).order_by(models.Ticket.fecha_creacion_ticket.desc()).all()
    
    return tickets

# --- 3. CHATBOT PÚBLICO ---

@router.post("/chatbot/ask", response_model=schemas.ChatbotResponse)
def public_chatbot(request: schemas.ChatbotRequest, db: Session = Depends(database.get_db)):
    """
    Chatbot simple para responder dudas ciudadanas.
    Lógica 'Fake' para Hackathon (Reglas simples).
    """
    msg = request.message.lower()
    response_text = ""
    actions = []

    # Lógica de respuestas predefinidas
    if "reportar" in msg or "denuncia" in msg:
        response_text = "Para realizar un reporte, ve a la sección 'Nuevo Reporte', toma una foto y selecciona tu municipio. ¡Es muy rápido!"
        actions = ["Crear Reporte"]
    
    elif "zona" in msg or "municipio" in msg:
        if request.context_zone_id:
            zona = db.query(models.Zona).filter(models.Zona.id_zona == request.context_zone_id).first()
            nombre = zona.nombre_zona if zona else "tu zona"
            response_text = f"Actualmente en {nombre} estamos enfocados en la limpieza de canales. ¿Viste algo irregular?"
        else:
            response_text = "Trabajamos en toda la Cuenca Lerma-Chapala. ¿Desde qué municipio nos escribes?"
            actions = ["Ver Mapa de Zonas"]
            
    elif "estatus" in msg or "mi reporte" in msg:
        response_text = "Puedes consultar el avance de tus denuncias en la pestaña 'Mis Reportes' usando el código de tu dispositivo."
        actions = ["Ver Mis Reportes"]
        
    else:
        response_text = "Hola, soy el asistente virtual de la Cuenca. Puedo ayudarte a reportar fugas, basura o consultar el estado de tus denuncias."
        actions = ["¿Cómo reportar?", "¿Qué zonas cubren?"]

    return {
        "response": response_text,
        "suggested_actions": actions
    }