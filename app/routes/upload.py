"""
Rutas de carga de archivos.
RF-01: El sistema permite subir archivos CSV o JSON.
RF-02: Validación de formato, columnas y tipos de datos.
RF-03: Procesamiento de datos con Pandas.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.validation import validate_and_parse
from app.services import analysis_service
from app import store

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/", summary="Cargar archivo de datos financieros (CU-01)")
async def cargar_archivo(archivo: UploadFile = File(...)):
    """
    **CU-01 / RF-01**: Sube un archivo CSV o JSON con datos de ventas o gastos.

    **Campos requeridos en el archivo:**
    - `fecha` — fecha del registro (ej: 2024-01-15)
    - `monto` — valor numérico (ventas o gastos)
    - `categoria` — tipo o categoría del registro

    El archivo se valida, se procesa con Pandas y queda disponible en memoria
    para consultar las métricas y reportes.
    """
    # ── Tamaño del archivo ────────────────────────────────────────────────────
    content = await archivo.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "archivo_muy_grande",
                "mensaje": "El archivo supera el límite de 50 MB.",
            },
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "archivo_vacio",
                "mensaje": "El archivo está vacío.",
            },
        )

    # ── RF-02: Validar y parsear ──────────────────────────────────────────────
    filename = archivo.filename or "archivo_sin_nombre"
    df = validate_and_parse(content, filename)

    # ── RF-03: Guardar en memoria (store) ─────────────────────────────────────
    ext = filename.rsplit(".", 1)[-1].lower()
    store.save(df, filename, ext)

    return {
        "mensaje": "Archivo cargado y validado correctamente.",
        "archivo": filename,
        "formato": ext,
        "registros_cargados": len(df),
        "columnas_detectadas": df.columns.tolist(),
        "rango_fechas": {
            "inicio": str(df["fecha"].min().date()),
            "fin": str(df["fecha"].max().date()),
        },
        "siguiente_paso": "Consulta /api/analysis/completo para ver el análisis.",
    }


@router.delete("/", summary="Limpiar datos en memoria")
def limpiar_datos():
    """Elimina los datos cargados actualmente en memoria."""
    if not store.has_data():
        raise HTTPException(status_code=404, detail={"mensaje": "No hay datos cargados."})
    store.clear()
    return {"mensaje": "Datos eliminados de memoria correctamente."}


@router.get("/status", summary="Estado de la carga actual")
def estado_carga():
    """Retorna información del archivo actualmente cargado en memoria."""
    if not store.has_data():
        return {"cargado": False, "mensaje": "No hay datos en memoria. Sube un archivo primero."}
    meta = store.get_meta()
    return {"cargado": True, **meta}
