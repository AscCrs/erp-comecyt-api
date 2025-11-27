from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

# check_same_thread=False solo es necesario para SQLite, para MySQL lo quitamos
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True, # Vital para evitar desconexiones en MySQL
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para inyectar la sesión en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()