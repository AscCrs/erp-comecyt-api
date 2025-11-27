from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, public, dashboard, operations
from .database import engine
from . import models

# Crear tablas si no existen (útil para desarrollo rápido)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ERP Resiliencia Ambiental API",
    version="1.0.0"
)

# Configuración CORS (Indispensable para Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los Routers
app.include_router(auth.router)
app.include_router(public.router) # Endpoints abiertos (Chatbot, Reportes)
app.include_router(dashboard.router) # Endpoints protegidos (BSC)
app.include_router(operations.router) # Endpoints protegidos (Tickets)

@app.get("/")
def root():
    return {"message": "API Online - ERP Resiliencia"}