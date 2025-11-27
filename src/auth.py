from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models, database, config

settings = config.get_settings()

# Configuración de Hashing (Bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticación de FastAPI (le dice a Swagger dónde obtener el token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- FUNCIONES DE HASHING ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña plana con su hash en BD."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash seguro para guardar en la BD."""
    return pwd_context.hash(password)

# --- FUNCIONES JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un JWT firmado con los datos del usuario."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agregamos la fecha de expiración al payload
    to_encode.update({"exp": expire})
    
    # Firmamos el token con nuestra SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- DEPENDENCIA DE PROTECCIÓN (EL GUARDIÁN) ---

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
) -> models.Usuario:
    """
    Esta función se ejecuta antes de cualquier endpoint protegido.
    1. Lee el token del Header 'Authorization'.
    2. Lo decodifica y valida la firma.
    3. Busca al usuario en la BD.
    Si algo falla, lanza un error 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub") # 'sub' suele guardar el ID o email
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Buscar usuario en BD
    user = db.query(models.Usuario).filter(models.Usuario.correo_usuario == email).first()
    if user is None:
        raise credentials_exception
        
    return user

class RoleChecker:
    """
    Clase para verificar roles de usuario en endpoints protegidos.
    Uso:
        @app.get("/admin-only")
        async def admin_endpoint(current_user: Usuario = Depends(RoleChecker(["admin"]))):
            ...
    """

    def __init__(self, allowed_roles: List[models.RolUsuario]):
        self.allowed_roles = allowed_roles

    """
    Esta clase funciona como dependencia.
    Si el usuario no tiene el rol adecuado, lanza un 403.
    """
    def __call__(self, user: models.Usuario = Depends(get_current_user)):
        if user.rol_usuario not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este recurso"
            )
        return user
    
# --- DEPENDENCIAS DE PERMISOS PREDEFINIDAS ---

allow_gobernanza = RoleChecker([models.RolUsuario.GOBERNANZA])

allow_gerencia = RoleChecker([models.RolUsuario.GOBERNANZA, models.RolUsuario.SUBGERENTE])

allow_operacion_full = RoleChecker([
    models.RolUsuario.GOBERNANZA,
    models.RolUsuario.SUBGERENTE,
    models.RolUsuario.GRUPO_SOCIAL,
])

allow_auditoria = RoleChecker([
    models.RolUsuario.GOBERNANZA,
    models.RolUsuario.SUBGERENTE,
    models.RolUsuario.GRUPO_SOCIAL,
    models.RolUsuario.AUDITOR,
])

allow_all_roles = get_current_user  # Cualquier usuario autenticado
