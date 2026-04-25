# tests/integration/test_analysis.py
"""
Pruebas de integración para endpoints /api/analysis
RF-04 a RF-08: Métricas, tendencias, comparaciones, outliers y periodos clave
RF-09: Exposición vía API REST
"""

import pytest
import tempfile
import pandas as pd
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestAnalysisIntegration:
    """Pruebas de integración para endpoints /api/analysis"""
    
    def setup_method(self):
        """Limpiar datos antes de cada prueba"""
        client.delete("/api/upload/")
    
    def test_metricas_requires_data(self):
        """Verifica que los endpoints requieran datos cargados"""
        response = client.get("/api/analysis/metricas")
        assert response.status_code == 404
        assert "sin_datos" in str(response.json()).lower()
    
    def test_metricas_returns_correct_data(self, sample_csv_valid):
        """Verifica que /api/analysis/metricas devuelva datos correctos"""
        # Cargar datos
        with open(sample_csv_valid, 'rb') as f:
            upload_response = client.post(
                "/api/upload/", 
                files={"archivo": ("datos.csv", f, "text/csv")}
            )
        assert upload_response.status_code == 200
        
        response = client.get("/api/analysis/metricas")
        assert response.status_code == 200
        
        data = response.json()
        # Usando sample_df_valid: Ene=4500, Feb=5500, Mar=5000, total=15000
        assert data["total_monto"] == 15000.0
        assert "categorias" in data
        assert "promedio_diario" in data
        assert "promedio_mensual" in data
        assert "total_registros" in data
    
    def test_tendencias_returns_correct_structure(self, sample_csv_valid):
        """Verifica que /api/analysis/tendencias devuelva estructura correcta"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/tendencias")
        assert response.status_code == 200
        
        data = response.json()
        assert "tendencias" in data
        assert len(data["tendencias"]) == 3
        
        # Verificar estructura de cada tendencia
        for tendencia in data["tendencias"]:
            assert "periodo" in tendencia
            assert "total_monto" in tendencia
            assert "tendencia" in tendencia
            assert "variacion_porcentual" in tendencia
    
    def test_comparacion_returns_correct_data(self, sample_csv_valid):
        """Verifica que /api/analysis/comparacion devuelva comparaciones"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/comparacion")
        assert response.status_code == 200
        
        data = response.json()
        assert "comparaciones" in data
        assert "total_comparaciones" in data
        assert len(data["comparaciones"]) == 2  # Ene-Feb, Feb-Mar
        
        # Verificar estructura de cada comparación
        for comp in data["comparaciones"]:
            assert "periodo_actual" in comp
            assert "periodo_anterior" in comp
            assert "variacion_porcentual" in comp
            assert "tendencia" in comp
    
    def test_outliers_with_custom_threshold(self, sample_df_with_outliers):
        """Verifica que /api/analysis/outliers acepte umbral personalizado"""
        import tempfile
        
        # Guardar dataframe con outliers
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_df_with_outliers.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("outliers.csv", csv_file, "text/csv")})
        
        # Probar con diferentes umbrales
        response_umbral_bajo = client.get("/api/analysis/outliers", params={"umbral": 1.0})
        response_umbral_alto = client.get("/api/analysis/outliers", params={"umbral": 3.0})
        
        assert response_umbral_bajo.status_code == 200
        assert response_umbral_alto.status_code == 200
        
        data_bajo = response_umbral_bajo.json()
        data_alto = response_umbral_alto.json()
        
        # Umbral más bajo debe detectar más outliers (o al menos no menos)
        assert data_bajo["total_outliers"] >= data_alto["total_outliers"]
    
    def test_outliers_default_threshold(self, sample_df_with_outliers):
        """Verifica que /api/analysis/outliers funcione con umbral por defecto (2.0)"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_df_with_outliers.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("outliers.csv", csv_file, "text/csv")})
        
        response = client.get("/api/analysis/outliers")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_outliers" in data
        assert "criterio" in data
        assert "valores_atipicos" in data
        
        # Debe detectar al menos el outlier de 10000
        assert data["total_outliers"] >= 1
    
    def test_periodos_clave_returns_correct_data(self, sample_csv_valid):
        """Verifica que /api/analysis/periodos-clave devuelva mejor y peor mes"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/periodos-clave")
        assert response.status_code == 200
        
        data = response.json()
        assert "mejor_periodo" in data
        assert "peor_periodo" in data
        assert "total_periodos_analizados" in data
        
        # Verificar estructura del mejor período
        assert "periodo" in data["mejor_periodo"]
        assert "total_monto" in data["mejor_periodo"]
        
        # Verificar estructura del peor período
        assert "periodo" in data["peor_periodo"]
        assert "total_monto" in data["peor_periodo"]
    
    def test_analisis_completo_returns_all_modules(self, sample_csv_valid):
        """Verifica que /api/analysis/completo incluya todos los módulos"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/completo")
        assert response.status_code == 200
        
        data = response.json()
        assert "fuente" in data
        assert "analisis" in data
        
        analisis = data["analisis"]
        expected_modules = [
            "metricas_generales",
            "tendencias_mensuales", 
            "comparacion_mes_a_mes",
            "outliers",
            "periodos_clave"
        ]
        
        for module in expected_modules:
            assert module in analisis, f"Falta el módulo: {module}"
    
    def test_analisis_completo_requires_data(self):
        """Verifica que /api/analysis/completo requiera datos cargados"""
        response = client.get("/api/analysis/completo")
        assert response.status_code == 404


class TestAnalysisEdgeCases:
    """Pruebas de casos borde para endpoints de análisis"""
    
    def setup_method(self):
        client.delete("/api/upload/")
    
    def test_metricas_con_un_solo_registro(self):
        """Verifica métricas con un solo registro"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01'],
            'monto': [1000000.0],
            'categoria': ['ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("unico.csv", csv_file, "text/csv")})
        
        response = client.get("/api/analysis/metricas")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_monto"] == 1000000.0
        assert data["promedio_diario"] == 1000000.0
        assert data["promedio_mensual"] == 1000000.0
        assert data["total_registros"] == 1
    
    def test_tendencias_con_un_solo_mes(self):
        """Verifica tendencias con un solo mes de datos"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'monto': [1000.0, 2000.0, 3000.0],
            'categoria': ['ventas', 'ventas', 'ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("un_mes.csv", csv_file, "text/csv")})
        
        response = client.get("/api/analysis/tendencias")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tendencias"]) == 1
        assert data["tendencias"][0]["tendencia"] == "sin_referencia"
        assert data["tendencias"][0]["variacion_porcentual"] is None
    
    def test_comparacion_con_un_solo_mes(self):
        """Verifica comparación con un solo mes (debe devolver lista vacía)"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'monto': [1000.0, 2000.0, 3000.0],
            'categoria': ['ventas', 'ventas', 'ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("un_mes.csv", csv_file, "text/csv")})
        
        response = client.get("/api/analysis/comparacion")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_comparaciones"] == 0
        assert len(data["comparaciones"]) == 0
    
    def test_outliers_sin_outliers(self):
        """Verifica detección de outliers cuando no hay valores anormales"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
            'monto': [1000.0, 1100.0, 1050.0, 1080.0],
            'categoria': ['ventas'] * 4
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("sin_outliers.csv", csv_file, "text/csv")})
        
        response = client.get("/api/analysis/outliers")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_outliers"] == 0
        assert len(data["valores_atipicos"]) == 0
    
    def test_periodos_clave_con_un_solo_mes(self):
        """Verifica periodos clave con un solo mes (mejor y peor son el mismo)"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'monto': [1000.0, 2000.0, 3000.0],
            'categoria': ['ventas', 'ventas', 'ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("un_mes.csv", csv_file, "text/csv")})
        
        response = client.get("/api/analysis/periodos-clave")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_periodos_analizados"] == 1
        assert data["mejor_periodo"]["periodo"] == data["peor_periodo"]["periodo"]
        assert data["mejor_periodo"]["total_monto"] == 6000.0


class TestAnalysisDataConsistency:
    """Pruebas de consistencia de datos entre endpoints"""
    
    def setup_method(self):
        client.delete("/api/upload/")
    
    def test_consistencia_metricas_tendencias(self, sample_csv_valid):
        """Verifica que métricas generales y tendencias sean consistentes"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        metricas = client.get("/api/analysis/metricas").json()
        tendencias = client.get("/api/analysis/tendencias").json()
        
        # La suma de los montos mensuales debe ser igual al total general
        total_mensual = sum(m["total_monto"] for m in tendencias["tendencias"])
        assert total_mensual == metricas["total_monto"]
    
    def test_consistencia_comparacion_tendencias(self, sample_csv_valid):
        """Verifica que comparaciones y tendencias sean consistentes"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        comparacion = client.get("/api/analysis/comparacion").json()
        tendencias = client.get("/api/analysis/tendencias").json()
        
        # La variación de comparación debe coincidir con la tendencia
        for comp in comparacion["comparaciones"]:
            # Buscar la tendencia correspondiente
            tendencia_mes = next(
                (t for t in tendencias["tendencias"] if t["periodo"] == comp["periodo_actual"]), 
                None
            )
            if tendencia_mes and comp["variacion_porcentual"] is not None:
                assert comp["variacion_porcentual"] == tendencia_mes["variacion_porcentual"]
    
    def test_consistencia_periodos_clave_tendencias(self, sample_csv_valid):
        """Verifica que periodos clave coincidan con tendencias"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        periodos = client.get("/api/analysis/periodos-clave").json()
        tendencias = client.get("/api/analysis/tendencias").json()
        
        # Encontrar el mes con mayor monto en tendencias
        mejor_tendencia = max(tendencias["tendencias"], key=lambda x: x["total_monto"])
        
        assert mejor_tendencia["periodo"] == periodos["mejor_periodo"]["periodo"]
        assert mejor_tendencia["total_monto"] == periodos["mejor_periodo"]["total_monto"]


# Para ejecutar solo estas pruebas:
# pytest tests/integration/test_analysis.py -v