# tests/unit/test_validation.py
import pytest
import pandas as pd
from app.utils.validation import validate_and_parse

class TestValidacionDatos:
    """Pruebas unitarias para RF-02: Validación de estructura y tipos de datos"""
    
    def test_valid_csv_structure(self, sample_csv_valid):
        """Verifica que un CSV con columnas correctas pase la validación"""
        with open(sample_csv_valid, 'rb') as f:
            content = f.read()
        
        df = validate_and_parse(content, "datos_validos.csv")
        
        assert df is not None
        assert len(df) == 6
        assert 'fecha' in df.columns
        assert 'monto' in df.columns
        assert 'categoria' in df.columns
    
    def test_valid_json_structure(self, sample_json_valid):
        """Verifica que un JSON con columnas correctas pase la validación"""
        with open(sample_json_valid, 'rb') as f:
            content = f.read()
        
        df = validate_and_parse(content, "datos_validos.json")
        
        assert df is not None
        assert len(df) == 6
        assert 'fecha' in df.columns
        assert 'monto' in df.columns
        assert 'categoria' in df.columns
    
    def test_empty_file_rejected(self, sample_csv_empty):
        """Verifica que archivos vacíos sean rechazados"""
        with open(sample_csv_empty, 'rb') as f:
            content = f.read()
        
        with pytest.raises(Exception) as exc_info:
            validate_and_parse(content, "vacio.csv")
        
        assert "vacío" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()
    
    def test_missing_required_columns_rejected(self, sample_csv_missing_columns):
        """Verifica que archivos sin columnas obligatorias sean rechazados"""
        with open(sample_csv_missing_columns, 'rb') as f:
            content = f.read()
        
        with pytest.raises(Exception) as exc_info:
            validate_and_parse(content, "columnas_faltantes.csv")
        
        error_msg = str(exc_info.value).lower()
        assert "categoria" in error_msg or "columna" in error_msg
    
    def test_invalid_date_format_rejected(self, sample_csv_invalid_date):
        """Verifica que fechas inválidas sean rechazadas"""
        with open(sample_csv_invalid_date, 'rb') as f:
            content = f.read()
        
        with pytest.raises(Exception) as exc_info:
            validate_and_parse(content, "fecha_invalida.csv")
        
        assert "fecha" in str(exc_info.value).lower()
    
    def test_non_numeric_monto_rejected(self, sample_csv_non_numeric):
        """Verifica que montos no numéricos sean rechazados"""
        with open(sample_csv_non_numeric, 'rb') as f:
            content = f.read()
        
        with pytest.raises(Exception) as exc_info:
            validate_and_parse(content, "monto_no_numerico.csv")
        
        assert "monto" in str(exc_info.value).lower() or "numeric" in str(exc_info.value).lower()
    
    def test_empty_category_rejected(self, sample_csv_empty_category):
        """Verifica que categorías vacías sean rechazadas"""
        with open(sample_csv_empty_category, 'rb') as f:
            content = f.read()
        
        with pytest.raises(Exception) as exc_info:
            validate_and_parse(content, "categoria_vacia.csv")
        
        assert "categoria" in str(exc_info.value).lower()
    
    def test_invalid_file_format(self, tmp_path):
        """Verifica que formatos no soportados sean rechazados"""
        txt_file = tmp_path / "archivo.txt"
        txt_file.write_text("fecha,monto,categoria\n2024-01-01,1000,ventas")
        
        with open(txt_file, 'rb') as f:
            content = f.read()
        
        with pytest.raises(Exception) as exc_info:
            validate_and_parse(content, "archivo.txt")
        
        assert "formato" in str(exc_info.value).lower() or "soportado" in str(exc_info.value).lower()