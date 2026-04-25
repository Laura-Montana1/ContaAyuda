# tests/unit/test_comparison.py
import pandas as pd
from app.services.analysis_service import comparar_meses

class TestComparacionMeses:
    """Pruebas unitarias para RF-06: Comparación mes a mes"""
    
    def test_calcula_variacion_correctamente(self):
        """Verifica que calcule la variación porcentual correcta"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [1000.0, 1000.0, 1500.0, 1500.0],  # Ene:2000, Feb:3000
            'categoria': ['ventas'] * 4
        })
        
        comparaciones = comparar_meses(df)
        
        assert len(comparaciones) == 1
        assert comparaciones[0]["periodo_anterior"] == "2024-01"
        assert comparaciones[0]["periodo_actual"] == "2024-02"
        assert comparaciones[0]["variacion_porcentual"] == 50.0
    
    def test_variacion_negativa(self):
        """Verifica variación negativa cuando hay caída"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [3000.0, 3000.0, 1000.0, 1000.0],  # Ene:6000, Feb:2000
            'categoria': ['ventas'] * 4
        })
        
        comparaciones = comparar_meses(df)
        
        assert comparaciones[0]["variacion_porcentual"] == -66.67
    
    def test_un_solo_mes_sin_comparaciones(self):
        """Verifica que con un solo mes no haya comparaciones"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15'],
            'monto': [1000.0, 2000.0],
            'categoria': ['ventas'] * 2
        })
        
        comparaciones = comparar_meses(df)
        
        assert len(comparaciones) == 0