"""
Rutas de análisis financiero.
RF-04 a RF-08: Métricas, tendencias, comparaciones, outliers y periodos clave.
RF-09: Exposición vía API REST con respuestas JSON.
"""

from fastapi import APIRouter, HTTPException, Query
from app.services import analysis_service
from app import store

router = APIRouter()


def _require_data():
    """Verifica que haya datos cargados o lanza 404."""
    if not store.has_data():
        raise HTTPException(
            status_code=404,
            detail={
                "error": "sin_datos",
                "mensaje": "No hay datos cargados. Usa POST /api/upload/ primero.",
            },
        )
    return store.get()


# ─────────────────────────────────────────────────────────────────────────────
# RF-04: Métricas generales
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/metricas", summary="RF-04 · Métricas generales (total, promedios)")
def metricas_generales():
    """
    Calcula:
    - **Total** de montos del período
    - **Promedio diario**
    - **Promedio mensual**
    - Desglose por categoría
    """
    df = _require_data()
    return analysis_service.calcular_metricas_generales(df)


# ─────────────────────────────────────────────────────────────────────────────
# RF-05: Tendencias mensuales
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/tendencias", summary="RF-05 · Tendencias mensuales")
def tendencias_mensuales():
    """
    Agrupa los datos por mes e identifica si cada período es de:
    - **crecimiento** (>5%)
    - **caída** (<-5%)
    - **estabilidad** (±5%)
    """
    df = _require_data()
    return {
        "tendencias": analysis_service.analizar_tendencias_mensuales(df)
    }


# ─────────────────────────────────────────────────────────────────────────────
# RF-06: Comparación mes a mes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/comparacion", summary="RF-06 · Comparación mes a mes")
def comparacion_mensual():
    """
    Calcula el **porcentaje de variación** entre cada mes y el anterior.
    El primer mes no tiene comparación disponible.
    """
    df = _require_data()
    comparaciones = analysis_service.comparar_meses(df)
    return {
        "total_comparaciones": len(comparaciones),
        "comparaciones": comparaciones,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RF-07: Detección de valores anormales
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/outliers", summary="RF-07 · Detección de valores atípicos")
def detectar_outliers(
    umbral: float = Query(
        default=2.0,
        ge=1.0,
        le=4.0,
        description="Número de desviaciones estándar para considerar un valor atípico (1.0 – 4.0)",
    )
):
    """
    Identifica días con montos **fuera del rango normal** usando desviación estándar.

    `umbral` (configurable): días cuyo monto diario está a más de `umbral`
    desviaciones estándar de la media son marcados como atípicos.
    """
    df = _require_data()
    return analysis_service.detectar_outliers(df, umbral_std=umbral)


# ─────────────────────────────────────────────────────────────────────────────
# RF-08: Mejores y peores periodos
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/periodos-clave", summary="RF-08 · Mejor y peor período mensual")
def periodos_clave():
    """
    Retorna el **mes con mayor monto acumulado** (mejor período)
    y el **mes con menor monto acumulado** (peor período).
    """
    df = _require_data()
    return analysis_service.identificar_periodos_clave(df)


# ─────────────────────────────────────────────────────────────────────────────
# RF-09: Análisis completo (todos los módulos)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/completo", summary="RF-09 · Análisis completo (todos los módulos)")
def analisis_completo():
    """
    Ejecuta **todos los módulos de análisis** en una sola llamada y retorna
    el resultado consolidado en formato JSON:

    - Métricas generales (RF-04)
    - Tendencias mensuales (RF-05)
    - Comparación mes a mes (RF-06)
    - Outliers (RF-07)
    - Períodos clave (RF-08)
    """
    df = _require_data()
    resultado = analysis_service.analisis_completo(df)
    return {
        "fuente": store.get_meta(),
        "analisis": resultado,
    }
