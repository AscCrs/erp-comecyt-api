from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# ==========================================
# 1. ENUMS (Validación Estricta)
# ==========================================

class TipoOrganizacion(str, Enum):
    ONG = "ONG"
    GOBIERNO = "GOBIERNO"
    UNIVERSIDAD = "UNIVERSIDAD"
    EMPRESA = "EMPRESA"

class RolUsuario(str, Enum):
    GOBERNANZA = "GOBERNANZA"
    SUBGERENTE = "SUBGERENTE"
    GRUPO_SOCIAL = "GRUPO_SOCIAL"
    AUDITOR = "AUDITOR"
    OPERADOR = "OPERADOR"

class PerspectivaBSC(str, Enum):
    FINANCIERA = "FINANCIERA"
    CLIENTES = "CLIENTES"
    PROCESOS = "PROCESOS"
    APRENDIZAJE = "APRENDIZAJE"

class ColorSemaforo(str, Enum):
    ROJO = "ROJO"
    AMARILLO = "AMARILLO"
    VERDE = "VERDE"

class TipoTransaccion(str, Enum):
    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
    PROPIO = "PROPIO"

class EstadoProyecto(str, Enum):
    PLANEACION = "PLANEACION"
    ACTIVO = "ACTIVO"
    FINALIZADO = "FINALIZADO"
    SUSPENDIDO = "SUSPENDIDO"

class Prioridad(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"

class CategoriaGasto(str, Enum):
    MATERIALES = "MATERIALES"
    LOGISTICA = "LOGISTICA"
    STAFF = "STAFF"
    TECNOLOGIA = "TECNOLOGIA"
    ELECTRICIDAD = "ELECTRICIDAD"
    SUELDOS = "SUELDOS"
    AGUA = "AGUA"
    OTROS = "OTROS"

class TipoIncidente(str, Enum):
    BASURA = "BASURA"
    FUGA = "FUGA"
    OLOR = "OLOR"
    QUIMICO = "QUIMICO"
    DESECHOS_RESIDUALES = "DESECHOS_RESIDUALES"
    TALA_IRREGULAR = "TALA_IRREGULAR"
    INCENDIOS_FORESTALES = "INCENDIOS_FORESTALES"
    OTRO = "OTRO"

class EstadoTicket(str, Enum):
    RECIBIDO = "RECIBIDO"
    ASIGNADO = "ASIGNADO"
    EN_PROCESO = "EN_PROCESO"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"

# ==========================================
# 2. SCHEMAS: ZONAS
# ==========================================

class ZonaBase(BaseModel):
    nombre_zona: str
    estado_zona: str

class ZonaResponse(ZonaBase):
    id_zona: int

    class Config:
        from_attributes = True

# ==========================================
# 3. SCHEMAS: ORGANIZACIONES
# ==========================================

class OrganizacionBase(BaseModel):
    nombre_organizacion: str
    tipo_organizacion: TipoOrganizacion

class OrganizacionCreate(OrganizacionBase):
    pass

class OrganizacionResponse(OrganizacionBase):
    id_organizacion: int
    fecha_creacion_organizacion: datetime

    class Config:
        from_attributes = True

# ==========================================
# 4. SCHEMAS: USUARIOS (Auth)
# ==========================================

class UsuarioBase(BaseModel):
    nombre_completo_usuario: str
    correo_usuario: EmailStr
    rol_usuario: RolUsuario = RolUsuario.OPERADOR
    id_organizacion_usuario: int

class UsuarioCreate(UsuarioBase):
    contraseña_usuario: str  # Solo visible al crear

class UsuarioLogin(BaseModel):
    correo_usuario: EmailStr
    contraseña_usuario: str

class UsuarioResponse(UsuarioBase):
    id_usuario: int
    fecha_creacion_usuario: datetime

    class Config:
        from_attributes = True

# ==========================================
# 5. SCHEMAS: BSC (Objetivos)
# ==========================================

class ObjetivoBase(BaseModel):
    titulo_objetivo: str
    perspectiva_objetivo: PerspectivaBSC
    kpi_nombre_objetivo: Optional[str] = None
    meta_valor_objetivo: float = 0.00
    avance_actual_objetivo: float = 0.00

class ObjetivoCreate(ObjetivoBase):
    id_organizacion_objetivo: int

class ObjetivoUpdate(BaseModel):
    avance_actual_objetivo: Optional[float] = None
    meta_valor_objetivo: Optional[float] = None
    color_semaforo_objetivo: Optional[ColorSemaforo] = None

class ObjetivoResponse(ObjetivoBase):
    id_objetivo: int
    color_semaforo_objetivo: ColorSemaforo
    fecha_creacion_objetivo: datetime

    class Config:
        from_attributes = True

# ==========================================
# 6. SCHEMAS: PROYECTOS
# ==========================================

class ProyectoBase(BaseModel):
    nombre_proyecto: str
    presupuesto_proyecto: float = 0.00
    estado_proyecto: EstadoProyecto = EstadoProyecto.PLANEACION
    prioridad_proyecto: Prioridad = Prioridad.MEDIA
    fecha_inicio_proyecto: Optional[date] = None
    fecha_fin_proyecto: Optional[date] = None

class ProyectoCreate(ProyectoBase):
    id_objetivo_proyecto: int
    id_organizacion_proyecto: int
    id_zona_proyecto: Optional[int] = None

class ProyectoResponse(ProyectoBase):
    id_proyecto: int
    # Podrías incluir el objetivo anidado si quisieras
    # objetivo: ObjetivoResponse 

    class Config:
        from_attributes = True

# ==========================================
# 7. SCHEMAS: FINANZAS (Transacciones y Gastos)
# ==========================================

class TransaccionCreate(BaseModel):
    id_organizacion_transaccion: int
    fuente_transaccion: Optional[str] = None
    monto_transaccion: float
    tipo_transaccion: TipoTransaccion
    fecha_transaccion: Optional[date] = None

class GastoCreate(BaseModel):
    id_proyecto_gasto: int
    monto_gasto: float
    concepto_gasto: str
    categoria_gasto: CategoriaGasto
    evidencia_url_gasto: Optional[str] = None

# ==========================================
# 8. SCHEMAS: TICKETS (Público y Privado)
# ==========================================

# Schema para la App Móvil (Ciudadano)
class TicketCreatePublic(BaseModel):
    id_usuario_reporte_ticket: str  # UUID del ciudadano
    descripcion_ticket: Optional[str] = None
    des_hechos_lugar_ticket: Optional[str] = None
    tipo_incidente_ticket: TipoIncidente
    id_zona_ticket: int  # El ID del municipio seleccionado
    ubicacion_lat_ticket: Optional[float] = None
    ubicacion_lon_ticket: Optional[float] = None
    evidence_base64: Optional[str] = None # Opcional: si envían la imagen en base64

# Schema para gestión interna (Operador)
class TicketUpdateInternal(BaseModel):
    estado_ticket: Optional[EstadoTicket] = None
    prioridad_ticket: Optional[Prioridad] = None
    id_proyecto_ticket: Optional[int] = None  # Asignación a proyecto

class TicketTransfer(BaseModel):
    nuevo_id_organizacion: int
    notas: Optional[str] = None

class TicketResponse(BaseModel):
    id_ticket: int
    tipo_incidente_ticket: TipoIncidente
    estado_ticket: EstadoTicket
    descripcion_ticket: Optional[str]
    fecha_creacion_ticket: datetime
    id_zona_ticket: Optional[int]
    # Se omiten datos sensibles del ciudadano

    class Config:
        from_attributes = True

# ==========================================
# TOKEN JWT
# ==========================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ==========================================
# 9. SCHEMAS: CHATBOT
# ==========================================

class ChatbotRequest(BaseModel):
    message: str
    user_uuid: Optional[str] = None # Para dar seguimiento a usuario

class ChatbotResponse(BaseModel):
    response: str
    suggested_actions: List[str] = [] # Ej: ["Crear Reporte", "Ver Mapa"]