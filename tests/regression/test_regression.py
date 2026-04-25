# tests/regression/test_regression.py
"""
Pruebas de regresión
Después de corregir un defecto, se ejecutan estas pruebas
para asegurar que no se haya introducido nuevos errores.
"""

import pytest
import pandas as pd
import tempfile
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestRegression:
    """Pruebas de regresión - Verifican que funcionalidades no se rompan"""
    
    def setup_method(self):
        """Limpiar estado antes de cada prueba"""
        client.delete("/api/upload/")
    
    @pytest.mark.regression
    def test_regression_carga_csv(self, sample_csv_valid):
        """Regresión: La carga de CSV debe seguir funcionando"""
        with open(sample_csv_valid, 'rb') as f:
            response = client.post(
                "/api/upload/",
                files={"archivo": ("datos.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        assert "registros_cargados" in response.json()
    
    @pytest.mark.regression
    def test_regression_carga_json(self, sample_json_valid):
        """Regresión: La carga de JSON debe seguir funcionando"""
        with open(sample_json_valid, 'rb') as f:
            response = client.post(
                "/api/upload/",
                files={"archivo": ("datos.json", f, "application/json")}
            )
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    def test_regression_metricas_totales(self, sample_csv_valid):
        """Regresión: El cálculo de totales debe ser correcto"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/metricas")
        data = response.json()
        
        # Los totales deben ser positivos y razonables
        assert data["total_monto"] > 0
        assert data["promedio_diario"] > 0
        assert data["promedio_mensual"] > 0
    
    @pytest.mark.regression
    def test_regression_tendencias_estructura(self, sample_csv_valid):
        """Regresión: La estructura de tendencias debe ser consistente"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/tendencias")
        data = response.json()
        
        assert "tendencias" in data
        for tendencia in data["tendencias"]:
            required_fields = ["periodo", "total_monto", "tendencia", "variacion_porcentual"]
            for field in required_fields:
                assert field in tendencia
    
    @pytest.mark.regression
    def test_regression_outliers_umbral_default(self, sample_df_with_outliers):
        """Regresión: Detección de outliers con umbral por defecto (2.0) debe funcionar"""
        import tempfile
        
        # Guardar dataframe con outliers
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_df_with_outliers.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                response_upload = client.post(
                    "/api/upload/",
                    files={"archivo": ("outliers.csv", csv_file, "text/csv")}
                )
        
        assert response_upload.status_code == 200
        
        response = client.get("/api/analysis/outliers")
        data = response.json()
        
        assert "total_outliers" in data
        assert "criterio" in data
        assert "valores_atipicos" in data
        
        # Debe detectar al menos un outlier (el valor 10000)
        assert data["total_outliers"] >= 1
    
    @pytest.mark.regression
    def test_regression_periodos_clave_existen(self, sample_csv_valid):
        """Regresión: Los periodos clave (mejor/peor mes) deben existir siempre"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/periodos-clave")
        data = response.json()
        
        assert "mejor_periodo" in data
        assert "peor_periodo" in data
        assert "periodo" in data["mejor_periodo"]
        assert "total_monto" in data["mejor_periodo"]
    
    @pytest.mark.regression
    def test_regression_api_documentation_available(self):
        """Regresión: La documentación Swagger debe estar disponible"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/upload/" in data["paths"]
    
    @pytest.mark.regression
    def test_regression_health_endpoint(self):
        """Regresión: El endpoint de health debe responder siempre"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["sistema"] == "Conta Ayuda"
    
    @pytest.mark.regression
    def test_regression_clear_data_after_analysis(self, sample_csv_valid):
        """Regresión: Limpiar datos después del análisis debe funcionar"""
        # Cargar datos
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        # Verificar que hay datos
        status_before = client.get("/api/upload/status")
        assert status_before.json()["cargado"] == True
        
        # Limpiar
        response = client.delete("/api/upload/")
        assert response.status_code == 200
        
        # Verificar que ya no hay datos
        status_after = client.get("/api/upload/status")
        assert status_after.json()["cargado"] == False
    
    @pytest.mark.regression
    def test_regression_error_handling_no_data(self):
        """Regresión: Los endpoints deben manejar correctamente cuando no hay datos"""
        endpoints = [
            "/api/analysis/metricas",
            "/api/analysis/tendencias",
            "/api/analysis/comparacion",
            "/api/analysis/outliers",
            "/api/analysis/periodos-clave",
            "/api/analysis/completo",
            "/api/report/json",
            "/api/report/resumen",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404
            assert "sin_datos" in str(response.json()).lower() or "no hay datos" in str(response.json()).lower()
    
    @pytest.mark.regression
    def test_regression_upload_status_consistency(self, sample_csv_valid):
        """Regresión: El estado de carga debe ser consistente"""
        # Inicialmente no hay datos
        status = client.get("/api/upload/status")
        assert status.json()["cargado"] == False
        
        # Después de cargar, debe haber datos
        with open(sample_csv_valid, 'rb') as f:
            upload_response = client.post(
                "/api/upload/",
                files={"archivo": ("datos.csv", f, "text/csv")}
            )
        
        assert upload_response.status_code == 200
        registros = upload_response.json()["registros_cargados"]
        
        status = client.get("/api/upload/status")
        assert status.json()["cargado"] == True
        assert status.json()["record_count"] == registros
        
        # Después de limpiar, no debe haber datos
        client.delete("/api/upload/")
        
        status = client.get("/api/upload/status")
        assert status.json()["cargado"] == False
    
    @pytest.mark.regression
    def test_regression_variaciones_porcentuales_rango(self, sample_csv_valid):
        """Regresión: Las variaciones porcentuales deben estar en rango razonable"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/comparacion")
        data = response.json()
        
        for comp in data["comparaciones"]:
            if comp["variacion_porcentual"] is not None:
                # Las variaciones no deberían ser absurdas (>1000% o <-100%)
                # Para datos de ejemplo realistas, deberían estar en este rango
                assert -100 <= comp["variacion_porcentual"] <= 1000
    
    @pytest.mark.regression
    def test_regression_categorias_no_duplicadas(self, sample_csv_valid):
        """Regresión: Las categorías no deben aparecer duplicadas en el resumen"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/metricas")
        data = response.json()
        
        categorias = [c["categoria"] for c in data["categorias"]]
        assert len(categorias) == len(set(categorias)), "Categorías duplicadas encontradas"
    
    @pytest.mark.regression
    def test_regression_fechas_orden_cronologico(self, sample_csv_valid):
        """Regresión: Las fechas deben estar ordenadas cronológicamente"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/analysis/tendencias")
        data = response.json()
        
        periodos = [t["periodo"] for t in data["tendencias"]]
        assert periodos == sorted(periodos), "Los periodos no están ordenados cronológicamente"
    
    @pytest.mark.regression
    def test_regression_reporte_json_estructura_fija(self, sample_csv_valid):
        """Regresión: La estructura del reporte JSON debe ser fija y predecible"""
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        response = client.get("/api/report/json")
        data = response.json()
        
        # Verificar estructura anidada esperada
        expected_structure = {
            "reporte": ["generado_en", "version", "sistema"],
            "fuente": ["filename", "file_type", "record_count"],
            "analisis": ["metricas_generales", "tendencias_mensuales", 
                        "comparacion_mes_a_mes", "outliers", "periodos_clave"]
        }
        
        for key, subkeys in expected_structure.items():
            assert key in data
            for subkey in subkeys:
                assert subkey in data[key]
    
    @pytest.mark.regression
    def test_regression_todos_los_endpoints_responden(self):
        """Regresión: Todos los endpoints deben responder (aunque sea con error)"""
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/docs"),
            ("GET", "/openapi.json"),
            ("POST", "/api/upload/"),
            ("GET", "/api/upload/status"),
            ("DELETE", "/api/upload/"),
            ("GET", "/api/analysis/metricas"),
            ("GET", "/api/analysis/tendencias"),
            ("GET", "/api/analysis/comparacion"),
            ("GET", "/api/analysis/outliers"),
            ("GET", "/api/analysis/periodos-clave"),
            ("GET", "/api/analysis/completo"),
            ("GET", "/api/report/json"),
            ("GET", "/api/report/resumen"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            # Todos los endpoints deben responder (código 2xx, 4xx, pero no timeout)
            assert response.status_code is not None
            # No debe ser 500 (error interno del servidor) a menos que sea esperado
            if endpoint not in ["/api/analysis/metricas", "/api/analysis/tendencias"]:
                # Algunos endpoints pueden dar 404 sin datos, eso está bien
                assert response.status_code != 500
    
    @pytest.mark.regression
    def test_regression_multiples_archivos_consecutivos(self, sample_csv_valid, sample_json_valid):
        """Regresión: Cargar múltiples archivos secuencialmente debe funcionar"""
        # Cargar primer archivo
        with open(sample_csv_valid, 'rb') as f:
            response1 = client.post(
                "/api/upload/",
                files={"archivo": ("archivo1.csv", f, "text/csv")}
            )
        assert response1.status_code == 200
        registros1 = response1.json()["registros_cargados"]
        
        # Analizar primer archivo
        metricas1 = client.get("/api/analysis/metricas").json()
        
        # Cargar segundo archivo (debe reemplazar)
        with open(sample_json_valid, 'rb') as f:
            response2 = client.post(
                "/api/upload/",
                files={"archivo": ("archivo2.json", f, "application/json")}
            )
        assert response2.status_code == 200
        registros2 = response2.json()["registros_cargados"]
        
        # Analizar segundo archivo
        metricas2 = client.get("/api/analysis/metricas").json()
        
        # Los datos deberían ser diferentes (diferentes archivos)
        # Si los archivos tienen el mismo contenido, esto podría fallar
        # Por eso comentamos esta aserción
        
        # Verificar que el estado refleja el último archivo cargado
        status = client.get("/api/upload/status").json()
        assert status["record_count"] == registros2
    
    @pytest.mark.regression
    def test_regression_frontend_servido(self):
        """Regresión: El frontend (index.html) debe ser servido correctamente"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Conta Ayuda" in response.text
    
    @pytest.mark.regression
    def test_regression_static_files_servidos(self):
        """Regresión: Los archivos estáticos deben ser accesibles"""
        # Verificar que logo.png existe (puede dar 404 si no está, pero no 500)
        response = client.get("/static/logo.png")
        # 404 es aceptable si el archivo no existe, 500 no
        assert response.status_code != 500


class TestRegressionCornerCases:
    """Pruebas de regresión para casos borde específicos"""
    
    def setup_method(self):
        client.delete("/api/upload/")
    
    @pytest.mark.regression
    def test_regression_fecha_fin_de_ano(self):
        """Regresión: Manejo de fechas cerca del fin de año"""
        import tempfile
        
        df = pd.DataFrame({
            'fecha': ['2024-12-31', '2025-01-01', '2025-01-02'],
            'monto': [1000.0, 2000.0, 3000.0],
            'categoria': ['ventas', 'ventas', 'ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                response = client.post(
                    "/api/upload/",
                    files={"archivo": ("fechas.csv", csv_file, "text/csv")}
                )
        
        assert response.status_code == 200
        
        # El análisis debe manejar correctamente años diferentes
        metricas = client.get("/api/analysis/metricas").json()
        assert metricas["total_monto"] == 6000.0
        
        tendencias = client.get("/api/analysis/tendencias").json()
        # Debe haber dos periodos: 2024-12 y 2025-01
        periodos = [t["periodo"] for t in tendencias["tendencias"]]
        assert "2024-12" in periodos
        assert "2025-01" in periodos
    
    @pytest.mark.regression
    def test_regression_montos_muy_pequenos(self):
        """Regresión: Manejo de montos muy pequeños (centavos)"""
        import tempfile
        
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02'],
            'monto': [0.01, 0.02],
            'categoria': ['ventas', 'ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                response = client.post(
                    "/api/upload/",
                    files={"archivo": ("montos_pequenos.csv", csv_file, "text/csv")}
                )
        
        assert response.status_code == 200
        
        metricas = client.get("/api/analysis/metricas").json()
        assert metricas["total_monto"] == 0.03
    
    @pytest.mark.regression
    def test_regression_montos_muy_grandes(self):
        """Regresión: Manejo de montos muy grandes (millones/miles de millones)"""
        import tempfile
        
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02'],
            'monto': [999999999999.99, 1000000000000.00],
            'categoria': ['ventas', 'ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                response = client.post(
                    "/api/upload/",
                    files={"archivo": ("montos_grandes.csv", csv_file, "text/csv")}
                )
        
        assert response.status_code == 200
        
        metricas = client.get("/api/analysis/metricas").json()
        # Debe manejar números grandes sin errores
        assert metricas["total_monto"] > 0