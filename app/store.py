"""
Almacén de datos en memoria.
El sistema no usa base de datos — los datos viven mientras dura la sesión (RF-01).
"""

import pandas as pd
from typing import Optional

# Estado global de la sesión (simple y suficiente para el alcance del proyecto)
_store: dict = {
    "df": None,            # DataFrame con los datos cargados
    "filename": None,      # Nombre del archivo cargado
    "file_type": None,     # "csv" | "json"
    "record_count": 0,
}


def save(df: pd.DataFrame, filename: str, file_type: str) -> None:
    _store["df"] = df
    _store["filename"] = filename
    _store["file_type"] = file_type
    _store["record_count"] = len(df)


def get() -> Optional[pd.DataFrame]:
    return _store["df"]


def get_meta() -> dict:
    return {
        "filename": _store["filename"],
        "file_type": _store["file_type"],
        "record_count": _store["record_count"],
    }


def clear() -> None:
    _store["df"] = None
    _store["filename"] = None
    _store["file_type"] = None
    _store["record_count"] = 0


def has_data() -> bool:
    return _store["df"] is not None
