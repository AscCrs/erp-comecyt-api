from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import database, schemas, models, auth, config

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)

@router.post("/login", response_model=schemas.Token) 
# Nota: Debes agregar la clase Token en tus schemas.py o usar un dict simple
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(database.get_db)
):
    """
    Endpoint para obtener el Token JWT (Login).
    
    - **username**: En tu caso, envía aquí el CORREO ELECTRÓNICO.
    - **password**: La contraseña del usuario.
    
    Retorna:
    - **access_token**: El JWT que debes guardar en Flutter (SecureStorage).
    - **token_type**: "bearer"
    """
    
    # 1. Buscar usuario por correo (form_data.username se mapea a correo_usuario)
    user = db.query(models.Usuario).filter(
        models.Usuario.correo_usuario == form_data.username
    ).first()
    
    # 2. Validar si el usuario existe y si la contraseña coincide (usando el hash)
    if not user or not auth.verify_password(form_data.password, user.contraseña_usuario):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Calcular tiempo de expiración
    settings = config.get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 4. Crear el Token JWT incluyendo datos útiles en el payload
    access_token = auth.create_access_token(
        data={
            "sub": user.correo_usuario,           # Subject (Identificador principal)
            "id_user": user.id_usuario,           # ID numérico
            "org_id": user.id_organizacion_usuario, # Para multi-tenant
            "rol": user.rol_usuario.value         # Para control de permisos (RBAC)
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register/admin", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_new_user_by_admin(
    new_user_data: schemas.UsuarioCreate, 
    db: Session = Depends(database.get_db),
    current_admin: models.Usuario = Depends(auth.allow_gobernanza)
):
    """
    Solo un usuario con rol GOBERNANZA puede crear nuevos usuarios
    y asignarles roles (Subgerente, Auditor, etc.)
    """
    
    # Validar correo duplicado
    user_exists = db.query(models.Usuario).filter(
        models.Usuario.correo_usuario == new_user_data.correo_usuario
    ).first()
    
    if user_exists:
        raise HTTPException(status_code=400, detail="El correo ya existe")

    # Hashear password
    hashed_password = auth.get_password_hash(new_user_data.contraseña_usuario)
    
    # Crear usuario con el ROL que viene en el JSON
    new_user = models.Usuario(
        id_organizacion_usuario=new_user_data.id_organizacion_usuario, 
        nombre_completo_usuario=new_user_data.nombre_completo_usuario,
        correo_usuario=new_user_data.correo_usuario,
        contraseña_usuario=hashed_password,
        rol_usuario=new_user_data.rol_usuario # Se respeta el rol enviado
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user