# tests/conftest.py
import pytest
import pandas as pd
import tempfile
import os
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Cliente de pruebas para FastAPI"""
    return TestClient(app)

@pytest.fixture
def sample_df_valid():
    """DataFrame válido para pruebas"""
    return pd.DataFrame({
        'fecha': ['2024-01-01', '2024-01-02', '2024-01-03', 
                  '2024-02-01', '2024-02-02', '2024-03-01'],
        'monto': [1000.0, 1500.0, 2000.0, 2500.0, 3000.0, 5000.0],
        'categoria': ['ventas', 'ventas', 'gastos', 'ventas', 'ventas', 'ventas']
    })

@pytest.fixture
def sample_csv_valid(tmp_path, sample_df_valid):
    """Archivo CSV válido temporal"""
    file_path = tmp_path / "datos_validos.csv"
    sample_df_valid.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def sample_json_valid(tmp_path, sample_df_valid):
    """Archivo JSON válido temporal"""
    file_path = tmp_path / "datos_validos.json"
    sample_df_valid.to_json(file_path, orient="records", date_format="iso")
    return file_path

@pytest.fixture
def sample_df_single_category():
    """DataFrame con una sola categoría"""
    return pd.DataFrame({
        'fecha': ['2024-01-01', '2024-01-02', '2024-02-01'],
        'monto': [1000.0, 2000.0, 3000.0],
        'categoria': ['ventas', 'ventas', 'ventas']
    })

@pytest.fixture
def sample_df_with_outliers():
    """DataFrame con valores atípicos"""
    # Media ~ 1857, desviación ~ 800
    return pd.DataFrame({
        'fecha': ['2024-01-01', '2024-01-02', '2024-01-03', 
                  '2024-01-04', '2024-01-05', '2024-01-06'],
        'monto': [1000.0, 1200.0, 1100.0, 1300.0, 10000.0, 900.0],  # 10000 es outlier
        'categoria': ['ventas'] * 6
    })

@pytest.fixture
def sample_csv_empty(tmp_path):
    """Archivo CSV vacío"""
    file_path = tmp_path / "vacio.csv"
    file_path.write_text("")
    return file_path

@pytest.fixture
def sample_csv_missing_columns(tmp_path):
    """CSV con columnas faltantes"""
    file_path = tmp_path / "columnas_faltantes.csv"
    file_path.write_text("fecha,monto\n2024-01-01,1000")
    return file_path

@pytest.fixture
def sample_csv_invalid_date(tmp_path):
    """CSV con fecha inválida"""
    file_path = tmp_path / "fecha_invalida.csv"
    file_path.write_text("fecha,monto,categoria\n2024-13-01,1000,ventas")
    return file_path

@pytest.fixture
def sample_csv_non_numeric(tmp_path):
    """CSV con monto no numérico"""
    file_path = tmp_path / "monto_no_numerico.csv"
    file_path.write_text("fecha,monto,categoria\n2024-01-01,abc,ventas")
    return file_path

@pytest.fixture
def sample_csv_empty_category(tmp_path):
    """CSV con categoría vacía"""
    file_path = tmp_path / "categoria_vacia.csv"
    file_path.write_text("fecha,monto,categoria\n2024-01-01,1000,")
    return file_path