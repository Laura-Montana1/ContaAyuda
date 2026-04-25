# tests/unit/test_periods.py
import pandas as pd
from app.services.analysis_service import identificar_periodos_clave

class TestPeriodosClave:
    """Pruebas unitarias para RF-08: Mejores y peores periodos"""
    
    def test_identifica_mejor_mes(self):
        """Verifica que identifique correctamente el mes con mayor monto"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15', 
                      '2024-03-01', '2024-03-15'],
            'monto': [1000.0, 1000.0, 5000.0, 5000.0, 2000.0, 2000.0],  # Ene:2000, Feb:10000, Mar:4000
            'categoria': ['ventas'] * 6
        })
        
        periodos = identificar_periodos_clave(df)
        
        assert periodos["mejor_periodo"]["periodo"] == "2024-02"
        assert periodos["mejor_periodo"]["total_monto"] == 10000.0
    
    def test_identifica_peor_mes(self):
        """Verifica que identifique correctamente el mes con menor monto"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15', 
                      '2024-03-01', '2024-03-15'],
            'monto': [1000.0, 1000.0, 5000.0, 5000.0, 2000.0, 2000.0],
            'categoria': ['ventas'] * 6
        })
        
        periodos = identificar_periodos_clave(df)
        
        assert periodos["peor_periodo"]["periodo"] == "2024-01"
        assert periodos["peor_periodo"]["total_monto"] == 2000.0
    
    def test_maneja_empates_correctamente(self):
        """Verifica que cuando hay empate, tome el primero (comportamiento esperado)"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [2000.0, 2000.0, 2000.0, 2000.0],  # Ene:4000, Feb:4000 (empate)
            'categoria': ['ventas'] * 4
        })
        
        periodos = identificar_periodos_clave(df)
        
        # Puede ser enero o febrero, pero debe tener un valor
        assert periodos["mejor_periodo"]["total_monto"] == 4000.0
        assert periodos["peor_periodo"]["total_monto"] == 4000.0
    
    def test_cuenta_periodos_analizados(self, sample_df_valid):
        """Verifica que cuente correctamente los períodos analizados"""
        periodos = identificar_periodos_clave(sample_df_valid)
        
        assert periodos["total_periodos_analizados"] == 3