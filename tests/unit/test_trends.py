# tests/unit/test_trends.py
import pandas as pd
from app.services.analysis_service import analizar_tendencias_mensuales

class TestTendenciasMensuales:
    """Pruebas unitarias para RF-05: Análisis de tendencias mensuales"""
    
    def test_agrupa_correctamente_por_mes(self, sample_df_valid):
        """Verifica que los datos se agrupen correctamente por mes"""
        tendencias = analizar_tendencias_mensuales(sample_df_valid)
        
        periodos = [t["periodo"] for t in tendencias]
        assert "2024-01" in periodos
        assert "2024-02" in periodos
        assert "2024-03" in periodos
    
    def test_detecta_crecimiento(self):
        """Verifica que detecte crecimiento cuando es >5%"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [1000.0, 1000.0, 3000.0, 3000.0],  # Ene:2000, Feb:6000 (200% aumento)
            'categoria': ['ventas'] * 4
        })
        
        tendencias = analizar_tendencias_mensuales(df)
        
        # El segundo mes (febrero) debe ser crecimiento
        assert tendencias[1]["tendencia"] == "crecimiento"
        assert tendencias[1]["variacion_porcentual"] == 200.0
    
    def test_detecta_caida(self):
        """Verifica que detecte caída cuando es <-5%"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [3000.0, 3000.0, 1000.0, 1000.0],  # Ene:6000, Feb:2000 (67% caída)
            'categoria': ['ventas'] * 4
        })
        
        tendencias = analizar_tendencias_mensuales(df)
        
        assert tendencias[1]["tendencia"] == "caida"
        assert tendencias[1]["variacion_porcentual"] == -66.67
    
    def test_detecta_estabilidad(self):
        """Verifica que detecte estabilidad cuando está entre -5% y 5%"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [1000.0, 1000.0, 1100.0, 1100.0],  # Ene:2000, Feb:2200 (10% -> dentro del rango? 10% >5% debería ser crecimiento)
            'categoria': ['ventas'] * 4
        })
        
        tendencias = analizar_tendencias_mensuales(df)
        
        # 10% es >5%, debería ser crecimiento, no estabilidad
        # Ajustar para estabilidad real
        df2 = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [1000.0, 1000.0, 1020.0, 1020.0],  # Ene:2000, Feb:2040 (2% cambio)
            'categoria': ['ventas'] * 4
        })
        
        tendencias2 = analizar_tendencias_mensuales(df2)
        assert tendencias2[1]["tendencia"] == "estabilidad"
    
    def test_primer_mes_sin_referencia(self, sample_df_valid):
        """Verifica que el primer mes tenga tendencia 'sin_referencia'"""
        tendencias = analizar_tendencias_mensuales(sample_df_valid)
        
        assert tendencias[0]["tendencia"] == "sin_referencia"
        assert tendencias[0]["variacion_porcentual"] is None
    
    def test_orden_cronologico(self):
        """Verifica que los meses aparezcan en orden cronológico"""
        df = pd.DataFrame({
            'fecha': ['2024-03-01', '2024-02-01', '2024-01-01', '2024-03-15'],
            'monto': [1000.0, 2000.0, 3000.0, 1000.0],
            'categoria': ['ventas'] * 4
        })
        
        tendencias = analizar_tendencias_mensuales(df)
        periodos = [t["periodo"] for t in tendencias]
        
        assert periodos == sorted(periodos)