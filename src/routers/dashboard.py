from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from .. import database, schemas, models, auth

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard (Privado)"]
)

# --- 1. ESTRATEGIA (BALANCED SCORECARD) ---

@router.get("/bsc/objetivos", response_model=List[schemas.ObjetivoResponse])
def get_strategic_objectives(
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Obtiene el tablero de objetivos estratégicos con su semáforo actual.
    Filtra SOLO los objetivos de la organización del usuario logueado.
    """
    objetivos = db.query(models.Objetivo).filter(
        models.Objetivo.id_organizacion_objetivo == current_user.id_organizacion_usuario
    ).all()
    return objetivos

@router.post("/bsc/objetivos", response_model=schemas.ObjetivoResponse)
def create_objective(
    objetivo: schemas.ObjetivoBase,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Crea un nuevo objetivo estratégico (ej. 'Saneamiento Río Lerma 2025').
    """
    new_obj = models.Objetivo(
        id_organizacion_objetivo=current_user.id_organizacion_usuario,
        titulo_objetivo=objetivo.titulo_objetivo,
        perspectiva_objetivo=objetivo.perspectiva_objetivo,
        kpi_nombre_objetivo=objetivo.kpi_nombre_objetivo,
        meta_valor_objetivo=objetivo.meta_valor_objetivo,
        avance_actual_objetivo=objetivo.avance_actual_objetivo,
        # Calculamos el color inicial
        color_semaforo_objetivo=calculate_semaphore(
            objetivo.avance_actual_objetivo, 
            objetivo.meta_valor_objetivo
        )
    )
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj

@router.patch("/bsc/objetivos/{id_objetivo}", response_model=schemas.ObjetivoResponse)
def update_objective_progress(
    id_objetivo: int,
    update_data: schemas.ObjetivoUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Endpoint CLAVE para el Hackathon: Permite actualizar manualmente el avance
    para ver cómo cambia el semáforo en tiempo real.
    """
    # 1. Buscar objetivo y verificar propiedad
    obj = db.query(models.Objetivo).filter(
        models.Objetivo.id_objetivo == id_objetivo,
        models.Objetivo.id_organizacion_objetivo == current_user.id_organizacion_usuario
    ).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo no encontrado")

    # 2. Actualizar campos
    if update_data.avance_actual_objetivo is not None:
        obj.avance_actual_objetivo = update_data.avance_actual_objetivo
    if update_data.meta_valor_objetivo is not None:
        obj.meta_valor_objetivo = update_data.meta_valor_objetivo

    # 3. Recalcular semáforo automáticamente
    obj.color_semaforo_objetivo = calculate_semaphore(
        obj.avance_actual_objetivo, 
        obj.meta_valor_objetivo
    )
    
    db.commit()
    db.refresh(obj)
    return obj

def calculate_semaphore(avance, meta):
    """Lógica simple para determinar el color del semáforo."""
    if meta == 0: 
        return models.ColorSemaforo.ROJO
    percentage = (avance / meta) * 100
    
    if percentage < 40:
        return models.ColorSemaforo.ROJO
    elif percentage < 80:
        return models.ColorSemaforo.AMARILLO
    else:
        return models.ColorSemaforo.VERDE

# --- 2. FINANZAS (PRESUPUESTO) ---

@router.get("/finanzas/resumen")
def get_financial_summary(
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Calcula el balance financiero en tiempo real:
    - Total Ingresos (Transacciones)
    - Total Asignado a Proyectos (Presupuesto Comprometido)
    - Total Gastado Real (Gastos registrados)
    """
    org_id = current_user.id_organizacion_usuario

    # A. Sumar todas las transacciones (Ingresos - Egresos Globales)
    total_billetera = db.query(func.sum(models.Transaccion.monto_transaccion))\
        .filter(models.Transaccion.id_organizacion_transaccion == org_id).scalar() or 0.0

    # B. Sumar presupuestos asignados a proyectos
    total_asignado = db.query(func.sum(models.Proyecto.presupuesto_proyecto))\
        .filter(models.Proyecto.id_organizacion_proyecto == org_id).scalar() or 0.0

    # C. Sumar gastos reales ejecutados
    # Hacemos un JOIN para asegurar que el gasto es de un proyecto de ESTA organización
    total_gastado = db.query(func.sum(models.Gasto.monto_gasto))\
        .join(models.Proyecto)\
        .filter(models.Proyecto.id_organizacion_proyecto == org_id).scalar() or 0.0

    return {
        "billetera_disponible": total_billetera,
        "presupuesto_comprometido": total_asignado,
        "gasto_real_ejecutado": total_gastado,
        "saldo_libre_para_proyectos": total_billetera - total_asignado
    }

@router.post("/finanzas/transacciones")
def add_transaction(
    transaccion: schemas.TransaccionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Inyectar fondos a la organización (ej. 'Donación recibida').
    Actualiza el monto económico del Home.
    """
    new_trans = models.Transaccion(
        id_organizacion_transaccion=current_user.id_organizacion_usuario, # Forzamos ID del usuario
        fuente_transaccion=transaccion.fuente_transaccion,
        monto_transaccion=transaccion.monto_transaccion,
        tipo_transaccion=transaccion.tipo_transaccion
    )
    db.add(new_trans)
    db.commit()
    return {"message": "Transacción registrada exitosamente"}

# --- 3. OPERACIÓN (PROYECTOS) ---

@router.get("/proyectos", response_model=List[schemas.ProyectoResponse])
def get_projects(
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Lista los proyectos operativos de la organización.
    """
    proyectos = db.query(models.Proyecto).filter(
        models.Proyecto.id_organizacion_proyecto == current_user.id_organizacion_usuario
    ).all()
    return proyectos

@router.post("/proyectos", response_model=schemas.ProyectoResponse)
def create_project(
    proyecto: schemas.ProyectoCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Crea un nuevo proyecto y lo vincula a un objetivo y zona.
    """
    # Validar que el Objetivo pertenezca a la misma organización (Seguridad)
    obj = db.query(models.Objetivo).filter(
        models.Objetivo.id_objetivo == proyecto.id_objetivo_proyecto,
        models.Objetivo.id_organizacion_objetivo == current_user.id_organizacion_usuario
    ).first()
    
    if not obj:
        raise HTTPException(status_code=400, detail="El objetivo estratégico no es válido")

    new_proj = models.Proyecto(
        id_objetivo_proyecto=proyecto.id_objetivo_proyecto,
        id_organizacion_proyecto=current_user.id_organizacion_usuario,
        id_zona_proyecto=proyecto.id_zona_proyecto,
        nombre_proyecto=proyecto.nombre_proyecto,
        presupuesto_proyecto=proyecto.presupuesto_proyecto,
        estado_proyecto=proyecto.estado_proyecto,
        prioridad_proyecto=proyecto.prioridad_proyecto,
        fecha_inicio_proyecto=proyecto.fecha_inicio_proyecto,
        fecha_fin_proyecto=proyecto.fecha_fin_proyecto
    )
    
    db.add(new_proj)
    db.commit()
    db.refresh(new_proj)
    return new_proj

# --- 4. IMPACTO (CLIENTES) ---

@router.get("/impacto/metricas")
def get_impact_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user)
):
    """
    Retorna contadores rápidos para el Dashboard de Impacto.
    """
    org_id = current_user.id_organizacion_usuario
    
    # Contar tickets por estado
    tickets_resueltos = db.query(models.Ticket).filter(
        models.Ticket.id_organizacion_ticket == org_id,
        models.Ticket.estado_ticket == models.EstadoTicket.RESUELTO
    ).count()
    
    tickets_abiertos = db.query(models.Ticket).filter(
        models.Ticket.id_organizacion_ticket == org_id,
        models.Ticket.estado_ticket != models.EstadoTicket.RESUELTO,
        models.Ticket.estado_ticket != models.EstadoTicket.CERRADO
    ).count()

    # Promedio de satisfacción (si hubiera datos en tabla Mediciones)
    # Aquí simulamos o tomamos el último valor manual ingresado
    ultima_medicion = db.query(models.Medicion).filter(
        models.Medicion.id_organizacion_medicion == org_id,
        models.Medicion.tipo_metrica_medicion == "SATISFACCION"
    ).order_by(models.Medicion.fecha_registro_medicion.desc()).first()
    
    satisfaccion = ultima_medicion.valor_medicion if ultima_medicion else 0.0

    return {
        "tickets_resueltos": tickets_resueltos,
        "tickets_activos": tickets_abiertos,
        "satisfaccion_ciudadana": satisfaccion
    }