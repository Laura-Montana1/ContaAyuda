# tests/integration/test_report.py
"""
Pruebas de integración para endpoint /api/report
CU-07: Generar reporte en JSON
RF-09: Exposición de resultados vía API REST
"""

import pytest
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestReportIntegration:
    """Pruebas de integración para endpoints de reportes"""
    
    def setup_method(self):
        """Limpiar datos antes de cada prueba"""
        client.delete("/api/upload/")
    
    def test_generar_reporte_json_requires_data(self):
        """Verifica que generar reporte requiera datos cargados"""
        response = client.get("/api/report/json")
        assert response.status_code == 404
        assert "sin_datos" in str(response.json())
    
    def test_generar_reporte_json_success(self, sample_csv_valid):
        """Verifica generación exitosa de reporte JSON"""
        # Cargar datos
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/report/json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "attachment; filename=" in response.headers["Content-Disposition"]
        
        data = response.json()
        
        # Verificar estructura del reporte
        assert "reporte" in data
        assert "fuente" in data
        assert "analisis" in data
        
        # Verificar metadatos del reporte
        assert "generado_en" in data["reporte"]
        assert data["reporte"]["sistema"] == "DataFinance Analyzer"
        assert data["reporte"]["version"] == "1.0.0"
        
        # Verificar análisis completo
        analisis = data["analisis"]
        assert "metricas_generales" in analisis
        assert "tendencias_mensuales" in analisis
        assert "comparacion_mes_a_mes" in analisis
        assert "outliers" in analisis
        assert "periodos_clave" in analisis
    
    def test_resumen_ejecutivo_returns_kpis(self, sample_csv_valid):
        """Verifica que el resumen ejecutivo devuelva KPIs correctos"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/report/resumen")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar KPIs
        assert "kpis" in data
        assert "total_monto" in data["kpis"]
        assert "promedio_diario" in data["kpis"]
        assert "promedio_mensual" in data["kpis"]
        assert "total_registros" in data["kpis"]
        
        # Verificar período analizado
        assert "periodo_analizado" in data
        assert "inicio" in data["periodo_analizado"]
        assert "fin" in data["periodo_analizado"]
        
        # Verificar mejor/peor mes
        assert "mejor_mes" in data
        assert "peor_mes" in data
        
        # Verificar alertas
        assert "alertas_outliers" in data
        assert "categorias_top" in data
    
    def test_resumen_ejecutivo_requires_data(self):
        """Verifica que resumen ejecutivo requiera datos cargados"""
        response = client.get("/api/report/resumen")
        assert response.status_code == 404
    
    def test_reporte_json_consistent_with_analysis(self, sample_csv_valid):
        """Verifica consistencia entre reporte JSON y análisis directo"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        # Obtener reporte
        reporte = client.get("/api/report/json").json()
        
        # Obtener análisis directo
        analisis = client.get("/api/analysis/completo").json()
        
        # Comparar resultados (deben ser consistentes)
        assert reporte["analisis"]["metricas_generales"]["total_monto"] == \
               analisis["analisis"]["metricas_generales"]["total_monto"]
        
        assert len(reporte["analisis"]["tendencias_mensuales"]) == \
               len(analisis["analisis"]["tendencias_mensuales"])
    
    def test_reporte_json_download_filename(self, sample_csv_valid):
        """Verifica que el archivo descargable tenga nombre correcto"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/report/json")
        
        assert "Content-Disposition" in response.headers
        filename = response.headers["Content-Disposition"]
        assert filename.startswith("attachment; filename=")
        assert "reporte_financiero_" in filename
        assert filename.endswith(".json")


class TestReportEdgeCases:
    """Pruebas de casos borde para reportes"""
    
    def setup_method(self):
        client.delete("/api/upload/")
    
    def test_reporte_con_datos_minimos(self):
        """Verifica reporte con datos mínimos (1 registro)"""
        import pandas as pd
        import tempfile
        
        df_minimo = pd.DataFrame({
            'fecha': ['2024-01-01'],
            'monto': [1000.0],
            'categoria': ['ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_minimo.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("minimo.csv", csv_file, "text/csv")})
        
        response = client.get("/api/report/json")
        assert response.status_code == 200
        
        data = response.json()
        assert data["analisis"]["metricas_generales"]["total_monto"] == 1000.0
        assert data["analisis"]["metricas_generales"]["total_registros"] == 1
    
    def test_reporte_despues_de_limpiar_datos(self, sample_csv_valid):
        """Verifica que después de limpiar, no se pueda generar reporte"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        # Limpiar datos
        client.delete("/api/upload/")
        
        # Intentar generar reporte
        response = client.get("/api/report/json")
        assert response.status_code == 404