"""
Conta Ayuda — Contabilidad y Análisis para tu PyMe
Sistema de análisis de ventas y gastos
Proyecto Ingeniería de Software 3 — Universidad Libre, Bogotá
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import upload, analysis, report

app = FastAPI(
    title="Conta Ayuda",
    description="Contabilidad y Análisis para tu PyMe — Sistema de análisis de ventas y gastos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rutas API
app.include_router(upload.router,   prefix="/api/upload",   tags=["1. Carga de Archivos"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["2. Análisis Financiero"])
app.include_router(report.router,   prefix="/api/report",   tags=["3. Reportes"])


@app.get("/", include_in_schema=False)
def frontend():
    """Sirve la interfaz principal de Conta Ayuda."""
    return FileResponse("static/index.html")


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "sistema": "Conta Ayuda"}
