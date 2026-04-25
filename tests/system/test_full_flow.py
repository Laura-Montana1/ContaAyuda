# tests/system/test_full_flow.py
"""
Pruebas de sistema - Flujos completos de usuario
Validan el flujo completo de principio a fin, simulando escenarios de usuario reales
"""

import pytest
import json
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestFullFlow:
    """Pruebas de flujo completo de usuario"""
    
    def setup_method(self):
        """Limpiar estado antes de cada prueba"""
        client.delete("/api/upload/")
    
    def test_flow_completo_ventas(self, sample_csv_valid):
        """
        Flujo completo usuario:
        1. Cargar archivo
        2. Verificar carga exitosa
        3. Consultar métricas
        4. Ver tendencias
        5. Ver comparaciones
        6. Ver outliers
        7. Descargar reporte
        """
        # ──────────────────────────────────────────────────────────────────────
        # PASO 1: Cargar archivo
        # ──────────────────────────────────────────────────────────────────────
        with open(sample_csv_valid, 'rb') as f:
            upload_response = client.post(
                "/api/upload/",
                files={"archivo": ("ventas.csv", f, "text/csv")}
            )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["mensaje"] == "Archivo cargado y validado correctamente."
        registros_cargados = upload_data["registros_cargados"]
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 2: Verificar estado de carga
        # ──────────────────────────────────────────────────────────────────────
        status_response = client.get("/api/upload/status")
        assert status_response.status_code == 200
        assert status_response.json()["cargado"] == True
        assert status_response.json()["record_count"] == registros_cargados
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 3: Consultar métricas generales (RF-04)
        # ──────────────────────────────────────────────────────────────────────
        metricas_response = client.get("/api/analysis/metricas")
        assert metricas_response.status_code == 200
        metricas = metricas_response.json()
        
        assert "total_monto" in metricas
        assert "promedio_diario" in metricas
        assert "promedio_mensual" in metricas
        assert "categorias" in metricas
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 4: Ver tendencias mensuales (RF-05)
        # ──────────────────────────────────────────────────────────────────────
        tendencias_response = client.get("/api/analysis/tendencias")
        assert tendencias_response.status_code == 200
        tendencias = tendencias_response.json()
        
        assert "tendencias" in tendencias
        for mes in tendencias["tendencias"]:
            assert "periodo" in mes
            assert "total_monto" in mes
            assert "tendencia" in mes
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 5: Ver comparaciones mes a mes (RF-06)
        # ──────────────────────────────────────────────────────────────────────
        comparacion_response = client.get("/api/analysis/comparacion")
        assert comparacion_response.status_code == 200
        comparacion = comparacion_response.json()
        
        assert "comparaciones" in comparacion
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 6: Ver detección de outliers (RF-07)
        # ──────────────────────────────────────────────────────────────────────
        outliers_response = client.get("/api/analysis/outliers")
        assert outliers_response.status_code == 200
        outliers = outliers_response.json()
        
        assert "total_outliers" in outliers
        assert "valores_atipicos" in outliers
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 7: Ver mejores/peores periodos (RF-08)
        # ──────────────────────────────────────────────────────────────────────
        periodos_response = client.get("/api/analysis/periodos-clave")
        assert periodos_response.status_code == 200
        periodos = periodos_response.json()
        
        assert "mejor_periodo" in periodos
        assert "peor_periodo" in periodos
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 8: Obtener análisis completo (RF-09)
        # ──────────────────────────────────────────────────────────────────────
        completo_response = client.get("/api/analysis/completo")
        assert completo_response.status_code == 200
        completo = completo_response.json()
        
        assert "fuente" in completo
        assert "analisis" in completo
        
        # ──────────────────────────────────────────────────────────────────────
        # PASO 9: Descargar reporte JSON (CU-07)
        # ──────────────────────────────────────────────────────────────────────
        reporte_response = client.get("/api/report/json")
        assert reporte_response.status_code == 200
        reporte = reporte_response.json()
        
        assert "reporte" in reporte
        assert "fuente" in reporte
        assert "analisis" in reporte
    
    def test_flow_con_json(self, sample_json_valid):
        """Flujo completo con archivo JSON en lugar de CSV"""
        with open(sample_json_valid, 'rb') as f:
            upload_response = client.post(
                "/api/upload/",
                files={"archivo": ("datos.json", f, "application/json")}
            )
        
        assert upload_response.status_code == 200
        
        # Verificar que el análisis funciona
        completo_response = client.get("/api/analysis/completo")
        assert completo_response.status_code == 200
    
    def test_flow_con_datos_gastos(self):
        """Flujo completo con datos de gastos"""
        import pandas as pd
        import tempfile
        
        df_gastos = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
            'monto': [500000.0, 300000.0, 600000.0, 400000.0],
            'categoria': ['gastos', 'gastos', 'gastos', 'gastos']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_gastos.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                upload_response = client.post(
                    "/api/upload/",
                    files={"archivo": ("gastos.csv", csv_file, "text/csv")}
                )
        
        assert upload_response.status_code == 200
        
        metricas = client.get("/api/analysis/metricas").json()
        assert metricas["total_monto"] == 1800000.0
        assert metricas["categorias"][0]["categoria"] == "gastos"
    
    def test_flow_con_error_recuperacion(self, sample_csv_valid, sample_csv_empty):
        """Flujo con error y recuperación"""
        # Intentar cargar archivo inválido
        with open(sample_csv_empty, 'rb') as f:
            error_response = client.post(
                "/api/upload/",
                files={"archivo": ("vacio.csv", f, "text/csv")}
            )
        
        assert error_response.status_code >= 400
        
        # El sistema debe permitir cargar un archivo válido después del error
        with open(sample_csv_valid, 'rb') as f:
            success_response = client.post(
                "/api/upload/",
                files={"archivo": ("datos.csv", f, "text/csv")}
            )
        
        assert success_response.status_code == 200
        
        # El análisis debe funcionar
        completo_response = client.get("/api/analysis/completo")
        assert completo_response.status_code == 200
    
    def test_flow_con_multiples_archivos(self, sample_csv_valid, sample_json_valid):
        """Flujo cargando múltiples archivos secuencialmente"""
        # Cargar primer archivo
        with open(sample_csv_valid, 'rb') as f:
            response1 = client.post(
                "/api/upload/",
                files={"archivo": ("archivo1.csv", f, "text/csv")}
            )
        assert response1.status_code == 200
        registros1 = response1.json()["registros_cargados"]
        
        # Cargar segundo archivo (sobrescribe el primero)
        with open(sample_json_valid, 'rb') as f:
            response2 = client.post(
                "/api/upload/",
                files={"archivo": ("archivo2.json", f, "application/json")}
            )
        assert response2.status_code == 200
        registros2 = response2.json()["registros_cargados"]
        
        # Verificar que el segundo reemplazó al primero
        status = client.get("/api/upload/status").json()
        assert status["record_count"] == registros2
        assert status["record_count"] != registros1
    
    def test_flow_limpiar_y_reiniciar(self, sample_csv_valid):
        """Flujo: cargar, analizar, limpiar, cargar nuevo archivo"""
        # Cargar y analizar primer archivo
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos1.csv", f, "text/csv")})
        
        metricas1 = client.get("/api/analysis/metricas").json()
        
        # Limpiar datos
        client.delete("/api/upload/")
        
        # Verificar que no hay datos
        status = client.get("/api/upload/status").json()
        assert status["cargado"] == False
        
        # Cargar y analizar segundo archivo (debería funcionar)
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos2.csv", f, "text/csv")})
        
        metricas2 = client.get("/api/analysis/metricas").json()
        
        # Ambos análisis deben dar el mismo resultado (mismo archivo)
        assert metricas1["total_monto"] == metricas2["total_monto"]


class TestFlowEdgeCases:
    """Pruebas de casos borde en flujos completos"""
    
    def setup_method(self):
        client.delete("/api/upload/")
    
    def test_flow_con_un_solo_registro(self):
        """Flujo con archivo de un solo registro"""
        import pandas as pd
        import tempfile
        
        df_unico = pd.DataFrame({
            'fecha': ['2024-01-01'],
            'monto': [1000000.0],
            'categoria': ['ventas']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_unico.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("unico.csv", csv_file, "text/csv")})
        
        # Verificar que el análisis funciona con un solo registro
        metricas = client.get("/api/analysis/metricas").json()
        assert metricas["total_monto"] == 1000000.0
        
        tendencias = client.get("/api/analysis/tendencias").json()
        assert len(tendencias["tendencias"]) == 1
        assert tendencias["tendencias"][0]["tendencia"] == "sin_referencia"
        
        comparacion = client.get("/api/analysis/comparacion").json()
        assert comparacion["total_comparaciones"] == 0
    
    def test_flow_con_datos_multi_categoria(self):
        """Flujo con múltiples categorías"""
        import pandas as pd
        import tempfile
        
        df_multicat = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
            'monto': [1000.0, 500.0, 2000.0, 300.0],
            'categoria': ['ventas', 'gastos', 'ventas', 'gastos']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_multicat.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("multicat.csv", csv_file, "text/csv")})
        
        metricas = client.get("/api/analysis/metricas").json()
        
        # Verificar categorías
        assert len(metricas["categorias"]) == 2
        categorias = {c["categoria"]: c["total_monto"] for c in metricas["categorias"]}
        assert categorias["ventas"] == 3000.0
        assert categorias["gastos"] == 800.0