"""
Ruta de generación de reportes.
CU-07: Generar reporte en formato JSON.
RF-09: Exposición de resultados vía API REST.
"""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services import analysis_service
from app import store

router = APIRouter()


@router.get("/json", summary="CU-07 · Generar reporte completo en JSON")
def generar_reporte_json():
    """
    Genera y entrega un **reporte completo** del análisis financiero en formato JSON.

    El reporte incluye:
    - Metadatos del archivo analizado
    - Métricas generales
    - Tendencias mensuales
    - Comparación mes a mes
    - Valores atípicos detectados
    - Períodos con mejor y peor desempeño
    - Timestamp de generación
    """
    if not store.has_data():
        raise HTTPException(
            status_code=404,
            detail={
                "error": "sin_datos",
                "mensaje": "No hay datos cargados. Usa POST /api/upload/ primero.",
            },
        )

    df = store.get()
    meta = store.get_meta()

    reporte = {
        "reporte": {
            "generado_en": datetime.now().isoformat(),
            "version": "1.0.0",
            "sistema": "DataFinance Analyzer",
        },
        "fuente": meta,
        "analisis": analysis_service.analisis_completo(df),
    }

    return JSONResponse(
        content=reporte,
        headers={
            "Content-Disposition": f'attachment; filename="reporte_financiero_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        },
    )


@router.get("/resumen", summary="Resumen ejecutivo del análisis")
def resumen_ejecutivo():
    """
    Retorna un **resumen ejecutivo** con los indicadores más importantes
    del análisis para uso en dashboards (CU-08).
    """
    if not store.has_data():
        raise HTTPException(
            status_code=404,
            detail={"mensaje": "No hay datos cargados."},
        )

    df = store.get()
    metricas = analysis_service.calcular_metricas_generales(df)
    periodos = analysis_service.identificar_periodos_clave(df)
    outliers = analysis_service.detectar_outliers(df)

    return {
        "kpis": {
            "total_monto": metricas["total_monto"],
            "promedio_diario": metricas["promedio_diario"],
            "promedio_mensual": metricas["promedio_mensual"],
            "total_registros": metricas["total_registros"],
        },
        "periodo_analizado": {
            "inicio": metricas["fecha_inicio"],
            "fin": metricas["fecha_fin"],
        },
        "mejor_mes": periodos["mejor_periodo"],
        "peor_mes": periodos["peor_periodo"],
        "alertas_outliers": outliers["total_outliers"],
        "categorias_top": metricas["categorias"][:3],
    }
