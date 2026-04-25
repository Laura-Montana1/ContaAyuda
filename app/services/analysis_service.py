"""
Servicio de análisis financiero.
Implementa todos los requerimientos de cálculo: RF-03 a RF-08.
"""

import pandas as pd
import numpy as np
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# RF-03: Procesamiento de datos
# ─────────────────────────────────────────────────────────────────────────────

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Asegura columnas derivadas necesarias para el análisis:
    - año_mes (período mensual como string 'YYYY-MM')
    - anio y mes como enteros
    """
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["año_mes"] = df["fecha"].dt.to_period("M").astype(str)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# RF-04: Cálculo de métricas generales
# ─────────────────────────────────────────────────────────────────────────────

def calcular_metricas_generales(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calcula:
    - Total de montos
    - Promedio diario
    - Promedio mensual
    - Conteo de registros
    - Rango de fechas
    """
    df = prepare_dataframe(df)

    total = float(df["monto"].sum())
    promedio_diario = float(df.groupby("fecha")["monto"].sum().mean())

    montos_mensuales = df.groupby("año_mes")["monto"].sum()
    promedio_mensual = float(montos_mensuales.mean())

    categorias = (
        df.groupby("categoria")["monto"]
        .agg(total="sum", registros="count")
        .reset_index()
        .rename(columns={"total": "total_monto", "registros": "num_registros"})
        .sort_values("total_monto", ascending=False)
        .to_dict(orient="records")
    )

    return {
        "total_monto": round(total, 2),
        "promedio_diario": round(promedio_diario, 2),
        "promedio_mensual": round(promedio_mensual, 2),
        "total_registros": int(len(df)),
        "fecha_inicio": str(df["fecha"].min().date()),
        "fecha_fin": str(df["fecha"].max().date()),
        "categorias": categorias,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RF-05: Análisis de tendencias mensuales
# ─────────────────────────────────────────────────────────────────────────────

def analizar_tendencias_mensuales(df: pd.DataFrame) -> list[dict]:
    """
    Agrupa por mes y clasifica la tendencia respecto al mes anterior:
    - crecimiento / caída / estabilidad
    """
    df = prepare_dataframe(df)
    mensual = (
        df.groupby("año_mes")["monto"]
        .sum()
        .reset_index()
        .rename(columns={"monto": "total_monto"})
    )
    mensual = mensual.sort_values("año_mes").reset_index(drop=True)

    resultados = []
    for i, row in mensual.iterrows():
        anterior = mensual.loc[i - 1, "total_monto"] if i > 0 else None
        if anterior is None:
            tendencia = "sin_referencia"
            variacion_pct = None
        else:
            if anterior == 0:
                variacion_pct = None
                tendencia = "estabilidad"
            else:
                variacion_pct = round(((row["total_monto"] - anterior) / anterior) * 100, 2)
                if variacion_pct > 5:
                    tendencia = "crecimiento"
                elif variacion_pct < -5:
                    tendencia = "caida"
                else:
                    tendencia = "estabilidad"

        resultados.append({
            "periodo": row["año_mes"],
            "total_monto": round(float(row["total_monto"]), 2),
            "tendencia": tendencia,
            "variacion_porcentual": variacion_pct,
        })

    return resultados


# ─────────────────────────────────────────────────────────────────────────────
# RF-06: Comparación mes a mes
# ─────────────────────────────────────────────────────────────────────────────

def comparar_meses(df: pd.DataFrame) -> list[dict]:
    """
    Retorna porcentaje de variación entre cada mes y el anterior.
    """
    tendencias = analizar_tendencias_mensuales(df)
    comparaciones = []
    for i, t in enumerate(tendencias):
        if i == 0:
            continue
        anterior = tendencias[i - 1]
        comparaciones.append({
            "periodo_actual": t["periodo"],
            "monto_actual": t["total_monto"],
            "periodo_anterior": anterior["periodo"],
            "monto_anterior": anterior["total_monto"],
            "variacion_porcentual": t["variacion_porcentual"],
            "tendencia": t["tendencia"],
        })
    return comparaciones


# ─────────────────────────────────────────────────────────────────────────────
# RF-07: Detección de valores anormales (outliers)
# ─────────────────────────────────────────────────────────────────────────────

def detectar_outliers(df: pd.DataFrame, umbral_std: float = 2.0) -> dict[str, Any]:
    """
    Detecta días con montos fuera del rango [media ± umbral_std * desviación estándar].
    El criterio umbral_std es configurable (RNF según especificación).
    """
    df = prepare_dataframe(df)
    diario = df.groupby("fecha")["monto"].sum().reset_index()
    diario.columns = ["fecha", "monto_diario"]

    media = diario["monto_diario"].mean()
    std = diario["monto_diario"].std()
    limite_superior = media + umbral_std * std
    limite_inferior = media - umbral_std * std

    outliers = diario[
        (diario["monto_diario"] > limite_superior) |
        (diario["monto_diario"] < limite_inferior)
    ].copy()

    outliers["tipo"] = outliers["monto_diario"].apply(
        lambda v: "pico_alto" if v > limite_superior else "pico_bajo"
    )
    outliers["desviaciones"] = ((outliers["monto_diario"] - media) / std).round(2)
    outliers["fecha"] = outliers["fecha"].dt.strftime("%Y-%m-%d")

    return {
        "criterio": {
            "umbral_desviaciones": umbral_std,
            "media_diaria": round(float(media), 2),
            "desviacion_estandar": round(float(std), 2),
            "limite_superior": round(float(limite_superior), 2),
            "limite_inferior": round(float(limite_inferior), 2),
        },
        "total_outliers": int(len(outliers)),
        "valores_atipicos": outliers[["fecha", "monto_diario", "tipo", "desviaciones"]]
        .rename(columns={"monto_diario": "monto"})
        .to_dict(orient="records"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# RF-08: Identificación de mejores y peores periodos
# ─────────────────────────────────────────────────────────────────────────────

def identificar_periodos_clave(df: pd.DataFrame) -> dict[str, Any]:
    """
    Identifica el mes con mayor y menor monto acumulado.
    """
    df = prepare_dataframe(df)
    mensual = (
        df.groupby("año_mes")["monto"]
        .sum()
        .reset_index()
        .rename(columns={"monto": "total_monto"})
        .sort_values("año_mes")
    )

    idx_max = mensual["total_monto"].idxmax()
    idx_min = mensual["total_monto"].idxmin()

    return {
        "mejor_periodo": {
            "periodo": mensual.loc[idx_max, "año_mes"],
            "total_monto": round(float(mensual.loc[idx_max, "total_monto"]), 2),
        },
        "peor_periodo": {
            "periodo": mensual.loc[idx_min, "año_mes"],
            "total_monto": round(float(mensual.loc[idx_min, "total_monto"]), 2),
        },
        "total_periodos_analizados": int(len(mensual)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Análisis completo (agrega todos los RF anteriores)
# ─────────────────────────────────────────────────────────────────────────────

def analisis_completo(df: pd.DataFrame) -> dict[str, Any]:
    """Ejecuta todos los módulos de análisis y retorna un objeto consolidado."""
    return {
        "metricas_generales": calcular_metricas_generales(df),
        "tendencias_mensuales": analizar_tendencias_mensuales(df),
        "comparacion_mes_a_mes": comparar_meses(df),
        "outliers": detectar_outliers(df),
        "periodos_clave": identificar_periodos_clave(df),
    }
