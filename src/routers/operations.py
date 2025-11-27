from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import database, schemas, models, auth

router = APIRouter(
    prefix="/operations",
    tags=["Operaciones (Gestión de Tickets y Gastos)"]
)

# --- 1. BANDEJA DE ENTRADA (TICKETS) ---

@router.get("/tickets/inbox", response_model=List[schemas.TicketResponse])
def get_tickets_inbox(
    estado: Optional[models.EstadoTicket] = None,
    zona_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Obtiene los tickets asignados a la organización del usuario.
    Permite filtrar por Estado (ej. solo 'RECIBIDO') o Zona.
    """
    query = db.query(models.Ticket).filter(
        models.Ticket.id_organizacion_ticket == current_user.id_organizacion_usuario
    )
    
    if estado:
        query = query.filter(models.Ticket.estado_ticket == estado)
    
    if zona_id:
        query = query.filter(models.Ticket.id_zona_ticket == zona_id)
        
    # Ordenar por fecha (más recientes primero)
    tickets = query.order_by(models.Ticket.fecha_creacion_ticket.desc()).all()
    return tickets

@router.get("/tickets/{ticket_id}", response_model=schemas.TicketResponse)
def get_ticket_detail(
    ticket_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Ver detalle de un ticket específico.
    Seguridad: Solo si pertenece a mi organización.
    """
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id_ticket == ticket_id,
        models.Ticket.id_organizacion_ticket == current_user.id_organizacion_usuario
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado o no tienes permiso")
        
    return ticket

# --- 2. GESTIÓN Y ASIGNACIÓN ---

@router.patch("/tickets/{ticket_id}/assign", response_model=schemas.TicketResponse)
def assign_ticket_to_project(
    ticket_id: int,
    update_data: schemas.TicketUpdateInternal,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Asigna un ticket a un Proyecto interno (ej. 'Brigada Limpieza Norte').
    Cambia el estado automáticamente a 'ASIGNADO'.
    """
    # 1. Buscar Ticket
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id_ticket == ticket_id,
        models.Ticket.id_organizacion_ticket == current_user.id_organizacion_usuario
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # 2. Validar Proyecto (Debe ser de la misma Org)
    if update_data.id_proyecto_ticket:
        project = db.query(models.Proyecto).filter(
            models.Proyecto.id_proyecto == update_data.id_proyecto_ticket,
            models.Proyecto.id_organizacion_proyecto == current_user.id_organizacion_usuario
        ).first()
        if not project:
            raise HTTPException(status_code=400, detail="El proyecto no es válido")
            
        ticket.id_proyecto_ticket = update_data.id_proyecto_ticket
        ticket.estado_ticket = models.EstadoTicket.ASIGNADO
    
    # 3. Actualizar otros campos (Prioridad, Estado manual)
    if update_data.prioridad_ticket:
        ticket.prioridad_ticket = update_data.prioridad_ticket
    if update_data.estado_ticket:
        ticket.estado_ticket = update_data.estado_ticket

    db.commit()
    db.refresh(ticket)
    return ticket

@router.patch("/tickets/{ticket_id}/transfer", response_model=schemas.TicketResponse)
def transfer_ticket_organization(
    ticket_id: int,
    transfer_data: schemas.TicketTransfer,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    REASIGNACIÓN (Derivación): Mueve el ticket a la bandeja de otra organización.
    Útil cuando un reporte llega por error a la entidad equivocada.
    """
    # 1. Buscar Ticket
    ticket = db.query(models.Ticket).filter(
        models.Ticket.id_ticket == ticket_id,
        models.Ticket.id_organizacion_ticket == current_user.id_organizacion_usuario
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # 2. Verificar que la Org destino exista
    target_org = db.query(models.Organizacion).filter(
        models.Organizacion.id_organizacion == transfer_data.nuevo_id_organizacion
    ).first()
    
    if not target_org:
        raise HTTPException(status_code=404, detail="Organización destino no existe")

    # 3. Realizar la transferencia
    # Cambiamos el dueño del ticket
    ticket.id_organizacion_ticket = transfer_data.nuevo_id_organizacion
    # Quitamos el proyecto asignado (porque el proyecto ID 5 de la Org A no existe en la Org B)
    ticket.id_proyecto_ticket = None 
    # Reseteamos estado
    ticket.estado_ticket = models.EstadoTicket.RECIBIDO
    
    # (Opcional) Podrías guardar un log de "transfer_data.notas" en una tabla de auditoría
    
    db.commit()
    db.refresh(ticket)
    return ticket

# --- 3. GASTOS OPERATIVOS ---

@router.post("/gastos", status_code=status.HTTP_201_CREATED)
def register_expense(
    gasto: schemas.GastoCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Registra un gasto vinculado a un proyecto.
    Esto resta presupuesto disponible en el Dashboard Financiero.
    """
    # 1. Validar que el proyecto pertenezca a mi organización
    project = db.query(models.Proyecto).filter(
        models.Proyecto.id_proyecto == gasto.id_proyecto_gasto,
        models.Proyecto.id_organizacion_proyecto == current_user.id_organizacion_usuario
    ).first()
    
    if not project:
        raise HTTPException(status_code=400, detail="Proyecto no válido o acceso denegado")

    # 2. Crear el Gasto
    new_expense = models.Gasto(
        id_proyecto_gasto=gasto.id_proyecto_gasto,
        monto_gasto=gasto.monto_gasto,
        concepto_gasto=gasto.concepto_gasto,
        categoria_gasto=gasto.categoria_gasto,
        evidencia_url_gasto=gasto.evidencia_url_gasto
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    return {"message": "Gasto registrado correctamente", "id_gasto": new_expense.id_gasto}

# --- 4. AYUDA PARA REASIGNACIÓN (ZONAS) ---

@router.get("/cobertura/sugerencias/{zona_id}")
def get_organizations_by_zone(
    zona_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Endpoint auxiliar para el Frontend:
    Si tengo un ticket de 'Lerma' (ID 17), ¿a qué organizaciones se lo puedo pasar?
    Devuelve lista de Orgs que tienen cobertura en esa zona.
    """
    zona = db.query(models.Zona).filter(models.Zona.id_zona == zona_id).first()
    if not zona:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
        
    # Usamos la relación Many-to-Many definida en models.py
    # zona.organizaciones trae la lista gracias a SQLAlchemy
    result = []
    for org in zona.organizaciones:
        # Excluir mi propia organización de la sugerencia
        if org.id_organizacion != current_user.id_organizacion_usuario:
            result.append({
                "id_organizacion": org.id_organizacion,
                "nombre": org.nombre_organizacion,
                "tipo": org.tipo_organizacion
            })
            
    return result