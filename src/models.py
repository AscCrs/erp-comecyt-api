from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Numeric, Text, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

# ==========================================
# 1. ENUMS (Deben coincidir con Pydantic)
# ==========================================

class TipoOrganizacion(str, enum.Enum):
    ONG = "ONG"
    GOBIERNO = "GOBIERNO"
    UNIVERSIDAD = "UNIVERSIDAD"
    EMPRESA = "EMPRESA"

class RolUsuario(str, enum.Enum):
    GOBERNANZA = "GOBERNANZA"
    SUBGERENTE = "SUBGERENTE"
    GRUPO_SOCIAL = "GRUPO_SOCIAL"
    AUDITOR = "AUDITOR"
    OPERADOR = "OPERADOR"

class PerspectivaBSC(str, enum.Enum):
    FINANCIERA = "FINANCIERA"
    CLIENTES = "CLIENTES"
    PROCESOS = "PROCESOS"
    APRENDIZAJE = "APRENDIZAJE"

class ColorSemaforo(str, enum.Enum):
    ROJO = "ROJO"
    AMARILLO = "AMARILLO"
    VERDE = "VERDE"

class TipoTransaccion(str, enum.Enum):
    PUBLICO = "PUBLICO"
    PRIVADO = "PRIVADO"
    PROPIO = "PROPIO"

class EstadoProyecto(str, enum.Enum):
    PLANEACION = "PLANEACION"
    ACTIVO = "ACTIVO"
    FINALIZADO = "FINALIZADO"
    SUSPENDIDO = "SUSPENDIDO"

class Prioridad(str, enum.Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"

class CategoriaGasto(str, enum.Enum):
    MATERIALES = "MATERIALES"
    LOGISTICA = "LOGISTICA"
    STAFF = "STAFF"
    TECNOLOGIA = "TECNOLOGIA"
    ELECTRICIDAD = "ELECTRICIDAD"
    SUELDOS = "SUELDOS"
    AGUA = "AGUA"
    OTROS = "OTROS"

class TipoIncidente(str, enum.Enum):
    BASURA = "BASURA"
    FUGA = "FUGA"
    OLOR = "OLOR"
    QUIMICO = "QUIMICO"
    DESECHOS_RESIDUALES = "DESECHOS_RESIDUALES"
    TALA_IRREGULAR = "TALA_IRREGULAR"
    INCENDIOS_FORESTALES = "INCENDIOS_FORESTALES"
    OTRO = "OTRO"

class EstadoTicket(str, enum.Enum):
    RECIBIDO = "RECIBIDO"
    ASIGNADO = "ASIGNADO"
    EN_PROCESO = "EN_PROCESO"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"

class TipoArchivo(str, enum.Enum):
    IMAGEN = "IMAGEN"
    VIDEO = "VIDEO"
    DOCUMENTO = "DOCUMENTO"

class FuenteDato(str, enum.Enum):
    ENCUESTA = "ENCUESTA"
    APP = "APP"
    EXTERNO = "EXTERNO"
    MANUAL = "MANUAL"

# ==========================================
# 2. TABLA INTERMEDIA (Muchos a Muchos)
# ==========================================
# Tabla de asociación pura entre Organizaciones y Zonas
cobertura_association = Table(
    'COBERTURA_ORGANIZACIONES',
    Base.metadata,
    Column('ID_ORGANIZACION', Integer, ForeignKey('ORGANIZACIONES.ID_ORGANIZACION', ondelete="CASCADE"), primary_key=True),
    Column('ID_ZONA', Integer, ForeignKey('ZONAS.ID_ZONA', ondelete="CASCADE"), primary_key=True)
)

# ==========================================
# 3. MODELOS (Tablas Principales)
# ==========================================

class Zona(Base):
    __tablename__ = "ZONAS"

    id_zona = Column("ID_ZONA", Integer, primary_key=True, autoincrement=True)
    nombre_zona = Column("NOMBRE_ZONA", String(100), nullable=False, index=True)
    estado_zona = Column("ESTADO_ZONA", String(50), nullable=False)

    # Relaciones
    tickets = relationship("Ticket", back_populates="zona")
    proyectos = relationship("Proyecto", back_populates="zona")
    # Relación M2M con Organizaciones
    organizaciones = relationship("Organizacion", secondary=cobertura_association, back_populates="zonas_cobertura")

class Organizacion(Base):
    __tablename__ = "ORGANIZACIONES"

    id_organizacion = Column("ID_ORGANIZACION", Integer, primary_key=True, autoincrement=True)
    nombre_organizacion = Column("NOMBRE_ORGANIZACION", String(100), nullable=False, index=True)
    tipo_organizacion = Column("TIPO_ORGANIZACION", Enum(TipoOrganizacion), nullable=False)
    fecha_creacion_organizacion = Column("FECHA_CREACION_ORGANIZACION", DateTime(timezone=True), server_default=func.now())

    # Relaciones
    usuarios = relationship("Usuario", back_populates="organizacion", cascade="all, delete-orphan")
    objetivos = relationship("Objetivo", back_populates="organizacion", cascade="all, delete-orphan")
    transacciones = relationship("Transaccion", back_populates="organizacion")
    proyectos = relationship("Proyecto", back_populates="organizacion", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="organizacion")
    mediciones = relationship("Medicion", back_populates="organizacion")
    
    # Cobertura geográfica (M2M)
    zonas_cobertura = relationship("Zona", secondary=cobertura_association, back_populates="organizaciones")

class Usuario(Base):
    __tablename__ = "USUARIOS"

    id_usuario = Column("ID_USUARIO", Integer, primary_key=True, autoincrement=True)
    id_organizacion_usuario = Column("ID_ORGANIZACION_USUARIO", Integer, ForeignKey("ORGANIZACIONES.ID_ORGANIZACION", ondelete="CASCADE"), nullable=False)
    nombre_completo_usuario = Column("NOMBRE_COMPLETO_USUARIO", String(100), nullable=False)
    correo_usuario = Column("CORREO_USUARIO", String(100), unique=True, nullable=False)
    contraseña_usuario = Column("CONTRASEÑA_USUARIO", String(255), nullable=False)
    rol_usuario = Column("ROL_USUARIO", Enum(RolUsuario), default=RolUsuario.OPERADOR)
    fecha_creacion_usuario = Column("FECHA_CREACION_USUARIO", DateTime(timezone=True), server_default=func.now())

    organizacion = relationship("Organizacion", back_populates="usuarios")

class Objetivo(Base):
    __tablename__ = "OBJETIVOS"

    id_objetivo = Column("ID_OBJETIVO", Integer, primary_key=True, autoincrement=True)
    id_organizacion_objetivo = Column("ID_ORGANIZACION_OBJETIVO", Integer, ForeignKey("ORGANIZACIONES.ID_ORGANIZACION", ondelete="CASCADE"), nullable=False)
    titulo_objetivo = Column("TITULO_OBJETIVO", String(150), nullable=False)
    perspectiva_objetivo = Column("PERSPECTIVA_OBJETIVO", Enum(PerspectivaBSC), nullable=False)
    kpi_nombre_objetivo = Column("KPI_NOMBRE_OBJETIVO", String(100), nullable=True)
    meta_valor_objetivo = Column("META_VALOR_OBJETIVO", Numeric(10, 2), default=0.00)
    avance_actual_objetivo = Column("AVANCE_ACTUAL_OBJETIVO", Numeric(10, 2), default=0.00)
    color_semaforo_objetivo = Column("COLOR_SEMAFORO_OBJETIVO", Enum(ColorSemaforo), default=ColorSemaforo.ROJO)
    fecha_creacion_objetivo = Column("FECHA_CREACION_OBJETIVO", DateTime(timezone=True), server_default=func.now())

    organizacion = relationship("Organizacion", back_populates="objetivos")
    proyectos = relationship("Proyecto", back_populates="objetivo")

class Transaccion(Base):
    __tablename__ = "TRANSACCIONES"

    id_transaccion = Column("ID_TRANSACCION", Integer, primary_key=True, autoincrement=True)
    id_organizacion_transaccion = Column("ID_ORGANIZACION_TRANSACCION", Integer, ForeignKey("ORGANIZACIONES.ID_ORGANIZACION"), nullable=False)
    fuente_transaccion = Column("FUENTE_TRANSACCION", String(100), nullable=True)
    monto_transaccion = Column("MONTO_TRANSACCION", Numeric(15, 2), nullable=False)
    tipo_transaccion = Column("TIPO_TRANSACCION", Enum(TipoTransaccion), nullable=False)
    fecha_transaccion = Column("FECHA_TRANSACCION", Date, server_default=func.current_date())

    organizacion = relationship("Organizacion", back_populates="transacciones")

class Proyecto(Base):
    __tablename__ = "PROYECTOS"

    id_proyecto = Column("ID_PROYECTO", Integer, primary_key=True, autoincrement=True)
    id_objetivo_proyecto = Column("ID_OBJETIVO_PROYECTO", Integer, ForeignKey("OBJETIVOS.ID_OBJETIVO"), nullable=False)
    id_organizacion_proyecto = Column("ID_ORGANIZACION_PROYECTO", Integer, ForeignKey("ORGANIZACIONES.ID_ORGANIZACION", ondelete="CASCADE"), nullable=False)
    id_zona_proyecto = Column("ID_ZONA_PROYECTO", Integer, ForeignKey("ZONAS.ID_ZONA", ondelete="SET NULL"), nullable=True)
    
    nombre_proyecto = Column("NOMBRE_PROYECTO", String(150), nullable=False)
    presupuesto_proyecto = Column("PRESUPUESTO_PROYECTO", Numeric(15, 2), default=0.00)
    estado_proyecto = Column("ESTADO_PROYECTO", Enum(EstadoProyecto), default=EstadoProyecto.PLANEACION)
    prioridad_proyecto = Column("PRIORIDAD_PROYECTO", Enum(Prioridad), default=Prioridad.MEDIA)
    fecha_inicio_proyecto = Column("FECHA_INICIO_PROYECTO", Date, nullable=True)
    fecha_fin_proyecto = Column("FECHA_FIN_PROYECTO", Date, nullable=True)

    organizacion = relationship("Organizacion", back_populates="proyectos")
    objetivo = relationship("Objetivo", back_populates="proyectos")
    zona = relationship("Zona", back_populates="proyectos")
    
    gastos = relationship("Gasto", back_populates="proyecto", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="proyecto")

class Gasto(Base):
    __tablename__ = "GASTOS"

    id_gasto = Column("ID_GASTO", Integer, primary_key=True, autoincrement=True)
    id_proyecto_gasto = Column("ID_PROYECTO_GASTO", Integer, ForeignKey("PROYECTOS.ID_PROYECTO", ondelete="CASCADE"), nullable=False)
    monto_gasto = Column("MONTO_GASTO", Numeric(12, 2), nullable=False)
    concepto_gasto = Column("CONCEPTO_GASTO", String(200), nullable=False)
    categoria_gasto = Column("CATEGORIA_GASTO", Enum(CategoriaGasto), default=CategoriaGasto.OTROS)
    evidencia_url_gasto = Column("EVIDENCIA_URL_GASTO", String(255), nullable=True)
    fecha_gasto = Column("FECHA_GASTO", Date, server_default=func.current_date())

    proyecto = relationship("Proyecto", back_populates="gastos")

class Ticket(Base):
    __tablename__ = "TICKETS"

    id_ticket = Column("ID_TICKET", Integer, primary_key=True, autoincrement=True)
    id_organizacion_ticket = Column("ID_ORGANIZACION_TICKET", Integer, ForeignKey("ORGANIZACIONES.ID_ORGANIZACION"), nullable=False)
    id_proyecto_ticket = Column("ID_PROYECTO_TICKET", Integer, ForeignKey("PROYECTOS.ID_PROYECTO", ondelete="SET NULL"), nullable=True)
    id_zona_ticket = Column("ID_ZONA_TICKET", Integer, ForeignKey("ZONAS.ID_ZONA", ondelete="SET NULL"), nullable=True)

    # Datos del Ciudadano
    id_usuario_reporte_ticket = Column("ID_USUARIO_REPORTE_TICKET", String(100), nullable=False)
    descripcion_ticket = Column("DESCRIPCION_TICKET", Text, nullable=True)
    des_hechos_lugar_ticket = Column("DES_HECHOS_LUGAR_TICKET", Text, nullable=True)
    
    tipo_incidente_ticket = Column("TIPO_INCIDENTE_TICKET", Enum(TipoIncidente), nullable=False)
    estado_ticket = Column("ESTADO_TICKET", Enum(EstadoTicket), default=EstadoTicket.RECIBIDO)
    prioridad_ticket = Column("PRIORIDAD_TICKET", Enum(Prioridad), default=Prioridad.MEDIA)
    
    ubicacion_lat_ticket = Column("UBICACION_LAT_TICKET", Numeric(9, 6), nullable=True)
    ubicacion_lon_ticket = Column("UBICACION_LON_TICKET", Numeric(9, 6), nullable=True)
    
    fecha_creacion_ticket = Column("FECHA_CREACION_TICKET", DateTime(timezone=True), server_default=func.now())
    fecha_cierre_ticket = Column("FECHA_CIERRE_TICKET", DateTime(timezone=True), nullable=True)

    organizacion = relationship("Organizacion", back_populates="tickets")
    proyecto = relationship("Proyecto", back_populates="tickets")
    zona = relationship("Zona", back_populates="tickets")
    evidencias = relationship("Evidencia", back_populates="ticket", cascade="all, delete-orphan")

class Evidencia(Base):
    __tablename__ = "EVIDENCIAS"

    id_evidencia = Column("ID_EVIDENCIA", Integer, primary_key=True, autoincrement=True)
    id_ticket_evidencia = Column("ID_TICKET_EVIDENCIA", Integer, ForeignKey("TICKETS.ID_TICKET", ondelete="CASCADE"), nullable=False)
    url_evidencia = Column("URL_EVIDENCIA", String(255), nullable=False)
    tipo_archivo_evidencia = Column("TIPO_ARCHIVO_EVIDENCIA", Enum(TipoArchivo), default=TipoArchivo.IMAGEN)
    fecha_carga_evidencia = Column("FECHA_CARGA_EVIDENCIA", DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="evidencias")

class Medicion(Base):
    __tablename__ = "MEDICIONES"

    id_medicion = Column("ID_MEDICION", Integer, primary_key=True, autoincrement=True)
    id_organizacion_medicion = Column("ID_ORGANIZACION_MEDICION", Integer, ForeignKey("ORGANIZACIONES.ID_ORGANIZACION", ondelete="CASCADE"), nullable=False)
    tipo_metrica_medicion = Column("TIPO_METRICA_MEDICION", String(100), nullable=False)
    valor_medicion = Column("VALOR_MEDICION", Numeric(10, 2), nullable=False)
    fuente_dato_medicion = Column("FUENTE_DATO_MEDICION", Enum(FuenteDato), default=FuenteDato.MANUAL)
    fecha_registro_medicion = Column("FECHA_REGISTRO_MEDICION", Date, server_default=func.current_date())
    notas_medicion = Column("NOTAS_MEDICION", Text, nullable=True)

    organizacion = relationship("Organizacion", back_populates="mediciones")