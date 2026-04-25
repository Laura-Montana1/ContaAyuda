"""
Utilidades de validación de archivos y datos.
RF-02: El sistema debe validar formato, columnas, tipos y calidad de datos.
RNF-05: Seguridad básica — evitar errores por archivos corruptos.
"""

import io
import json
import pandas as pd
from fastapi import HTTPException


# Campos mínimos requeridos según RF-01
REQUIRED_COLUMNS = {"fecha", "monto", "categoria"}

# Formatos de fecha aceptados
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d/%m/%y",
]


def _try_parse_date(series: pd.Series) -> pd.Series:
    """Intenta parsear una columna de fechas probando varios formatos."""
    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(series, format=fmt, errors="raise")
            return parsed
        except Exception:
            continue
    # Último intento con inferencia automática
    parsed = pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
    return parsed


def validate_and_parse(content: bytes, filename: str) -> pd.DataFrame:
    """
    Lee y valida el archivo (CSV o JSON).
    Retorna un DataFrame limpio o lanza HTTPException con mensaje descriptivo.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # ── RF-02: formato soportado ──────────────────────────────────────────────
    if ext not in ("csv", "json"):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "formato_no_soportado",
                "mensaje": f"El formato '.{ext}' no está soportado. Use CSV o JSON.",
                "formatos_aceptados": ["csv", "json"],
            },
        )

    # ── Parseo del archivo ────────────────────────────────────────────────────
    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            data = json.loads(content)
            # Acepta lista de objetos o {"datos": [...]}
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Busca la primera clave cuyo valor sea una lista
                list_key = next(
                    (k for k, v in data.items() if isinstance(v, list)), None
                )
                if list_key:
                    df = pd.DataFrame(data[list_key])
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Estructura JSON no reconocida.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "archivo_ilegible",
                "mensaje": f"No se pudo leer el archivo: {str(e)}",
            },
        )

    # ── RF-02: archivo vacío ──────────────────────────────────────────────────
    if df.empty:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "archivo_vacio",
                "mensaje": "El archivo no contiene registros.",
            },
        )

    # ── RF-02: normalizar nombres de columnas (minúsculas, sin espacios) ──────
    df.columns = [c.strip().lower() for c in df.columns]

    # ── RF-02: columnas requeridas ────────────────────────────────────────────
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "columnas_faltantes",
                "mensaje": f"Faltan las columnas requeridas: {sorted(missing)}",
                "columnas_requeridas": sorted(REQUIRED_COLUMNS),
                "columnas_encontradas": sorted(df.columns.tolist()),
            },
        )

    # ── RF-02: monto numérico ─────────────────────────────────────────────────
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    invalid_montos = df["monto"].isna().sum()
    if invalid_montos > 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "monto_invalido",
                "mensaje": f"{invalid_montos} registros tienen 'monto' no numérico.",
                "accion": "Revise que la columna 'monto' contenga solo valores numéricos.",
            },
        )

    # ── RF-02: fecha válida ───────────────────────────────────────────────────
    df["fecha"] = _try_parse_date(df["fecha"].astype(str))
    invalid_dates = df["fecha"].isna().sum()
    if invalid_dates > 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "fecha_invalida",
                "mensaje": f"{invalid_dates} registros tienen 'fecha' con formato inválido.",
                "formatos_aceptados": DATE_FORMATS,
            },
        )

    # ── RF-02: categoría no vacía ─────────────────────────────────────────────
    df["categoria"] = df["categoria"].astype(str).str.strip()
    empty_cats = (df["categoria"] == "").sum()
    if empty_cats > 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "categoria_vacia",
                "mensaje": f"{empty_cats} registros tienen 'categoría' vacía.",
            },
        )

    return df
