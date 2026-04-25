# tests/unit/test_metrics.py
import pytest
from app.services.analysis_service import calcular_metricas_generales

class TestMetricasGenerales:
    """Pruebas unitarias para RF-04: Cálculo de métricas generales"""
    
    def test_calcular_total_correcto(self, sample_df_valid):
        """Verifica que el total se calcule correctamente"""
        metricas = calcular_metricas_generales(sample_df_valid)
        
        # Total esperado: 1000+1500+2000+2500+3000+5000 = 15000
        assert metricas["total_monto"] == 15000.0
    
    def test_calcular_promedio_diario(self, sample_df_valid):
        """Verifica el cálculo del promedio diario"""
        metricas = calcular_metricas_generales(sample_df_valid)
        
        # Promedio por día: monto por fecha (no por registro individual)
        # Días: 2024-01-01(1000), 2024-01-02(1500), 2024-01-03(2000),
        #       2024-02-01(2500), 2024-02-02(3000), 2024-03-01(5000)
        # Promedio = 15000 / 6 = 2500
        assert metricas["promedio_diario"] == 2500.0
    
    def test_calcular_promedio_mensual(self, sample_df_valid):
        """Verifica el cálculo del promedio mensual"""
        metricas = calcular_metricas_generales(sample_df_valid)
        
        # Montos por mes: Ene=4500, Feb=5500, Mar=5000
        # Promedio = (4500+5500+5000)/3 = 5000
        assert metricas["promedio_mensual"] == 5000.0
    
    def test_calcular_con_datos_vacios(self):
        """Verifica que datos vacíos manejen correctamente"""
        df_vacio = pd.DataFrame({'fecha': [], 'monto': [], 'categoria': []})
        
        metricas = calcular_metricas_generales(df_vacio)
        
        assert metricas["total_monto"] == 0.0
        assert metricas["promedio_diario"] == 0.0
        assert metricas["promedio_mensual"] == 0.0
    
    def test_desglose_por_categoria(self, sample_df_valid):
        """Verifica que el desglose por categoría sea correcto"""
        metricas = calcular_metricas_generales(sample_df_valid)
        
        categorias = metricas["categorias"]
        # Buscar categoría ventas
        ventas = next((c for c in categorias if c["categoria"] == "ventas"), None)
        gastos = next((c for c in categorias if c["categoria"] == "gastos"), None)
        
        assert ventas is not None
        assert ventas["total_monto"] == 13000.0  # 1000+1500+2500+3000+5000
        assert gastos is not None
        assert gastos["total_monto"] == 2000.0
    
    def test_rango_fechas_correcto(self, sample_df_valid):
        """Verifica que el rango de fechas sea correcto"""
        metricas = calcular_metricas_generales(sample_df_valid)
        
        assert metricas["fecha_inicio"] == "2024-01-01"
        assert metricas["fecha_fin"] == "2024-03-01"