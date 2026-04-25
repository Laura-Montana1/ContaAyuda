# tests/performance/test_performance.py
"""
Pruebas de rendimiento (RNF-01)
Medir el tiempo de respuesta del sistema al procesar archivos de:
- 100 registros
- 10,000 registros
- 100,000 registros

Objetivo: Procesar un archivo de 100,000 registros en menos de 10 segundos
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestPerformance:
    """Pruebas de rendimiento para diferentes volúmenes de datos"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_performance_100_registros(self):
        """Rendimiento con 100 registros (debe ser < 1 segundo)"""
        df = self._generar_datos_prueba(100)
        tiempos = self._medir_tiempos_procesamiento(df)
        
        print(f"\n📊 100 registros:")
        print(f"   ├─ Carga: {tiempos['carga']:.4f} segundos")
        print(f"   ├─ Análisis: {tiempos['analisis']:.4f} segundos")
        print(f"   ├─ Reporte: {tiempos['reporte']:.4f} segundos")
        print(f"   └─ Total: {tiempos['total']:.4f} segundos")
        
        # Debe procesar 100 registros en menos de 1 segundo
        assert tiempos['total'] < 1.0, f"Tiempo excedido: {tiempos['total']:.2f}s"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_performance_10000_registros(self):
        """Rendimiento con 10,000 registros (debe ser < 2 segundos)"""
        df = self._generar_datos_prueba(10000)
        tiempos = self._medir_tiempos_procesamiento(df)
        
        print(f"\n📊 10,000 registros:")
        print(f"   ├─ Carga: {tiempos['carga']:.4f} segundos")
        print(f"   ├─ Análisis: {tiempos['analisis']:.4f} segundos")
        print(f"   ├─ Reporte: {tiempos['reporte']:.4f} segundos")
        print(f"   └─ Total: {tiempos['total']:.4f} segundos")
        
        # Debe procesar 10,000 registros en menos de 2 segundos
        assert tiempos['total'] < 2.0, f"Tiempo excedido: {tiempos['total']:.2f}s"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_performance_100000_registros(self):
        """Rendimiento con 100,000 registros (debe ser < 10 segundos)"""
        df = self._generar_datos_prueba(100000)
        tiempos = self._medir_tiempos_procesamiento(df)
        
        print(f"\n📊 100,000 registros:")
        print(f"   ├─ Carga: {tiempos['carga']:.4f} segundos")
        print(f"   ├─ Análisis: {tiempos['analisis']:.4f} segundos")
        print(f"   ├─ Reporte: {tiempos['reporte']:.4f} segundos")
        print(f"   └─ Total: {tiempos['total']:.4f} segundos")
        
        # RNF-01: Procesar 100,000 registros en menos de 10 segundos
        assert tiempos['total'] < 10.0, f"Tiempo excedido: {tiempos['total']:.2f}s"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_performance_500000_registros(self):
        """Rendimiento con 500,000 registros (benchmark adicional)"""
        df = self._generar_datos_prueba(500000)
        tiempos = self._medir_tiempos_procesamiento(df)
        
        print(f"\n📊 500,000 registros (Benchmark):")
        print(f"   ├─ Carga: {tiempos['carga']:.4f} segundos")
        print(f"   ├─ Análisis: {tiempos['analisis']:.4f} segundos")
        print(f"   ├─ Reporte: {tiempos['reporte']:.4f} segundos")
        print(f"   └─ Total: {tiempos['total']:.4f} segundos")
        
        # Sin umbral específico, solo medir para referencia
        # Pero debe ser razonable (< 45 segundos)
        assert tiempos['total'] < 45.0, f"Tiempo excedido para 500k registros: {tiempos['total']:.2f}s"
    
    def _generar_datos_prueba(self, n_registros: int) -> pd.DataFrame:
        """Genera datos de prueba con n registros"""
        np.random.seed(42)  # Para resultados reproducibles
        
        # Generar fechas (distribuidas en 12 meses)
        fechas_inicio = pd.Timestamp('2024-01-01')
        fechas = [fechas_inicio + pd.Timedelta(days=np.random.randint(0, 365)) 
                  for _ in range(n_registros)]
        
        # Generar montos (distribución normal alrededor de 1,000,000)
        montos = np.random.normal(1000000, 300000, n_registros).round(2)
        montos = np.abs(montos)  # Sin montos negativos
        
        # Generar categorías
        categorias = np.random.choice(['ventas', 'gastos', 'inversion', 'impuestos'], 
                                       n_registros, p=[0.7, 0.2, 0.05, 0.05])
        
        return pd.DataFrame({
            'fecha': fechas,
            'monto': montos,
            'categoria': categorias
        })
    
    def _medir_tiempos_procesamiento(self, df: pd.DataFrame) -> dict:
        """Mide los tiempos de carga, análisis y reporte del dataframe"""
        tiempos = {}
        
        # Guardar dataframe a CSV temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            # ──────────────────────────────────────────────────────────────────
            # Medir tiempo de carga (POST /api/upload/)
            # ──────────────────────────────────────────────────────────────────
            inicio_carga = time.time()
            with open(f.name, 'rb') as csv_file:
                upload_response = client.post(
                    "/api/upload/",
                    files={"archivo": ("datos_prueba.csv", csv_file, "text/csv")}
                )
            tiempos['carga'] = time.time() - inicio_carga
            
            assert upload_response.status_code == 200, f"Error en carga: {upload_response.status_code}"
            upload_data = upload_response.json()
            registros_cargados = upload_data.get("registros_cargados", 0)
            print(f"   📁 Registros cargados: {registros_cargados}")
            
            # ──────────────────────────────────────────────────────────────────
            # Medir tiempo de análisis completo (GET /api/analysis/completo)
            # ──────────────────────────────────────────────────────────────────
            inicio_analisis = time.time()
            analysis_response = client.get("/api/analysis/completo")
            tiempos['analisis'] = time.time() - inicio_analisis
            
            assert analysis_response.status_code == 200, f"Error en análisis: {analysis_response.status_code}"
            
            # ──────────────────────────────────────────────────────────────────
            # Medir tiempo de generación de reporte (GET /api/report/json)
            # ──────────────────────────────────────────────────────────────────
            inicio_reporte = time.time()
            report_response = client.get("/api/report/json")
            tiempos['reporte'] = time.time() - inicio_reporte
            
            assert report_response.status_code == 200, f"Error en reporte: {report_response.status_code}"
        
        # Limpiar después de la prueba
        client.delete("/api/upload/")
        
        tiempos['total'] = tiempos['carga'] + tiempos['analisis'] + tiempos['reporte']
        
        return tiempos


class TestPerformanceEndpoints:
    """Pruebas de rendimiento de endpoints individuales"""
    
    def setup_method(self):
        """Cargar datos antes de las pruebas de endpoints"""
        client.delete("/api/upload/")
        df = self._generar_datos_prueba(10000)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("datos.csv", csv_file, "text/csv")})
    
    def _generar_datos_prueba(self, n_registros: int) -> pd.DataFrame:
        """Genera datos de prueba con n registros"""
        np.random.seed(42)
        fechas_inicio = pd.Timestamp('2024-01-01')
        fechas = [fechas_inicio + pd.Timedelta(days=np.random.randint(0, 365)) 
                  for _ in range(n_registros)]
        montos = np.random.normal(1000000, 300000, n_registros).round(2)
        montos = np.abs(montos)
        categorias = np.random.choice(['ventas', 'gastos', 'inversion', 'impuestos'], 
                                       n_registros, p=[0.7, 0.2, 0.05, 0.05])
        
        return pd.DataFrame({
            'fecha': fechas,
            'monto': montos,
            'categoria': categorias
        })
    
    @pytest.mark.performance
    def test_endpoint_metricas_performance(self):
        """Rendimiento del endpoint /api/analysis/metricas"""
        inicio = time.time()
        response = client.get("/api/analysis/metricas")
        tiempo = time.time() - inicio
        
        print(f"\n📊 Endpoint /metrics: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 0.5, f"Endpoint lento: {tiempo:.2f}s"
    
    @pytest.mark.performance
    def test_endpoint_tendencias_performance(self):
        """Rendimiento del endpoint /api/analysis/tendencias"""
        inicio = time.time()
        response = client.get("/api/analysis/tendencias")
        tiempo = time.time() - inicio
        
        print(f"📊 Endpoint /tendencias: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 0.5, f"Endpoint lento: {tiempo:.2f}s"
    
    @pytest.mark.performance
    def test_endpoint_comparacion_performance(self):
        """Rendimiento del endpoint /api/analysis/comparacion"""
        inicio = time.time()
        response = client.get("/api/analysis/comparacion")
        tiempo = time.time() - inicio
        
        print(f"📊 Endpoint /comparacion: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 0.5, f"Endpoint lento: {tiempo:.2f}s"
    
    @pytest.mark.performance
    def test_endpoint_outliers_performance(self):
        """Rendimiento del endpoint /api/analysis/outliers"""
        inicio = time.time()
        response = client.get("/api/analysis/outliers")
        tiempo = time.time() - inicio
        
        print(f"📊 Endpoint /outliers: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 0.5, f"Endpoint lento: {tiempo:.2f}s"
    
    @pytest.mark.performance
    def test_endpoint_periodos_clave_performance(self):
        """Rendimiento del endpoint /api/analysis/periodos-clave"""
        inicio = time.time()
        response = client.get("/api/analysis/periodos-clave")
        tiempo = time.time() - inicio
        
        print(f"📊 Endpoint /periodos-clave: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 0.5, f"Endpoint lento: {tiempo:.2f}s"
    
    @pytest.mark.performance
    def test_endpoint_completo_performance(self):
        """Rendimiento del endpoint /api/analysis/completo"""
        inicio = time.time()
        response = client.get("/api/analysis/completo")
        tiempo = time.time() - inicio
        
        print(f"📊 Endpoint /completo: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 1.0, f"Endpoint completo lento: {tiempo:.2f}s"
    
    @pytest.mark.performance
    def test_endpoint_reporte_json_performance(self):
        """Rendimiento del endpoint /api/report/json"""
        inicio = time.time()
        response = client.get("/api/report/json")
        tiempo = time.time() - inicio
        
        print(f"📊 Endpoint /report/json: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 1.0, f"Reporte JSON lento: {tiempo:.2f}s"
    
    @pytest.mark.performance
    def test_endpoint_resumen_performance(self):
        """Rendimiento del endpoint /api/report/resumen"""
        inicio = time.time()
        response = client.get("/api/report/resumen")
        tiempo = time.time() - inicio
        
        print(f"📊 Endpoint /report/resumen: {tiempo:.4f} segundos")
        
        assert response.status_code == 200
        assert tiempo < 0.3, f"Resumen ejecutivo lento: {tiempo:.2f}s"


class TestPerformanceConcurrent:
    """Pruebas de rendimiento con peticiones concurrentes"""
    
    def setup_method(self):
        """Cargar datos antes de las pruebas concurrentes"""
        client.delete("/api/upload/")
        df = self._generar_datos_prueba(10000)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            f.flush()
            
            with open(f.name, 'rb') as csv_file:
                client.post("/api/upload/", files={"archivo": ("datos.csv", csv_file, "text/csv")})
    
    def _generar_datos_prueba(self, n_registros: int) -> pd.DataFrame:
        """Genera datos de prueba con n registros"""
        np.random.seed(42)
        fechas_inicio = pd.Timestamp('2024-01-01')
        fechas = [fechas_inicio + pd.Timedelta(days=np.random.randint(0, 365)) 
                  for _ in range(n_registros)]
        montos = np.random.normal(1000000, 300000, n_registros).round(2)
        montos = np.abs(montos)
        categorias = np.random.choice(['ventas', 'gastos'], n_registros, p=[0.7, 0.3])
        
        return pd.DataFrame({
            'fecha': fechas,
            'monto': montos,
            'categoria': categorias
        })
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_requests_10(self):
        """Prueba 10 peticiones concurrentes al mismo endpoint"""
        import concurrent.futures
        
        def hacer_peticion():
            inicio = time.time()
            response = client.get("/api/analysis/metricas")
            tiempo = time.time() - inicio
            return tiempo, response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futuros = [executor.submit(hacer_peticion) for _ in range(10)]
            
            tiempos = []
            for futuro in concurrent.futures.as_completed(futuros):
                tiempo, status = futuro.result()
                tiempos.append(tiempo)
                assert status == 200
        
        tiempo_promedio = sum(tiempos) / len(tiempos)
        tiempo_maximo = max(tiempos)
        
        print(f"\n📊 10 peticiones concurrentes:")
        print(f"   ├─ Promedio: {tiempo_promedio:.4f}s")
        print(f"   └─ Máximo: {tiempo_maximo:.4f}s")
        
        assert tiempo_promedio < 0.5, f"Tiempo promedio alto: {tiempo_promedio:.2f}s"
        assert tiempo_maximo < 1.0, f"Tiempo máximo alto: {tiempo_maximo:.2f}s"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_mixed_endpoints(self):
        """Prueba peticiones concurrentes a diferentes endpoints"""
        import concurrent.futures
        
        endpoints = [
            "/api/analysis/metricas",
            "/api/analysis/tendencias",
            "/api/analysis/comparacion",
            "/api/analysis/outliers",
            "/api/analysis/periodos-clave",
        ]
        
        def hacer_peticion(endpoint):
            inicio = time.time()
            response = client.get(endpoint)
            tiempo = time.time() - inicio
            return endpoint, tiempo, response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 2 peticiones por cada endpoint
            futuros = []
            for endpoint in endpoints:
                for _ in range(2):
                    futuros.append(executor.submit(hacer_peticion, endpoint))
            
            resultados = {}
            for futuro in concurrent.futures.as_completed(futuros):
                endpoint, tiempo, status = futuro.result()
                if endpoint not in resultados:
                    resultados[endpoint] = []
                resultados[endpoint].append(tiempo)
                assert status == 200
        
        print(f"\n📊 Peticiones concurrentes a múltiples endpoints:")
        for endpoint, tiempos in resultados.items():
            print(f"   ├─ {endpoint}: prom={sum(tiempos)/len(tiempos):.4f}s, max={max(tiempos):.4f}s")
        
        # Verificar que todos los endpoints respondieron rápido
        for endpoint, tiempos in resultados.items():
            assert max(tiempos) < 1.0, f"Endpoint {endpoint} lento en concurrencia"


class TestPerformanceScalability:
    """Pruebas de escalabilidad - comparación de tiempos con diferentes volúmenes"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_scalability_comparison(self):
        """Compara tiempos de procesamiento para diferentes volúmenes"""
        volúmenes = [100, 1000, 5000, 10000, 50000, 100000]
        resultados = []
        
        print("\n📊 📈 PRUEBA DE ESCALABILIDAD")
        print("=" * 60)
        print(f"{'Registros':<12} {'Carga (s)':<12} {'Análisis (s)':<14} {'Reporte (s)':<12} {'Total (s)':<10}")
        print("-" * 60)
        
        for n in volúmenes:
            df = self._generar_datos_prueba(n)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                f.flush()
                
                # Medir solo carga y análisis (sin limpiar entre mediciones)
                with open(f.name, 'rb') as csv_file:
                    inicio_carga = time.time()
                    upload_response = client.post(
                        "/api/upload/",
                        files={"archivo": (f"datos_{n}.csv", csv_file, "text/csv")}
                    )
                    tiempo_carga = time.time() - inicio_carga
                
                if upload_response.status_code == 200:
                    inicio_analisis = time.time()
                    analysis_response = client.get("/api/analysis/completo")
                    tiempo_analisis = time.time() - inicio_analisis
                    
                    inicio_reporte = time.time()
                    report_response = client.get("/api/report/json")
                    tiempo_reporte = time.time() - inicio_reporte
                    
                    tiempo_total = tiempo_carga + tiempo_analisis + tiempo_reporte
                    
                    resultados.append({
                        'registros': n,
                        'carga': tiempo_carga,
                        'analisis': tiempo_analisis,
                        'reporte': tiempo_reporte,
                        'total': tiempo_total
                    })
                    
                    print(f"{n:<12} {tiempo_carga:<12.4f} {tiempo_analisis:<14.4f} {tiempo_reporte:<12.4f} {tiempo_total:<10.4f}")
                else:
                    print(f"{n:<12} ERROR en carga")
            
            client.delete("/api/upload/")
        
        print("=" * 60)
        
        # Verificar que el crecimiento es razonable (sub-lineal)
        if len(resultados) >= 2:
            # Comparar 1000 vs 100000 (debería ser menos de 100x más lento)
            registros_1000 = next((r for r in resultados if r['registros'] == 1000), None)
            registros_100k = next((r for r in resultados if r['registros'] == 100000), None)
            
            if registros_1000 and registros_100k:
                factor = registros_100k['total'] / registros_1000['total']
                print(f"\n📊 Factor de crecimiento (1000 → 100,000 registros): {factor:.2f}x")
                # El factor debería ser menor que 100 (crecimiento sub-lineal)
                assert factor < 100, f"Crecimiento super-lineal detectado: {factor:.2f}x"
    
    def _generar_datos_prueba(self, n_registros: int) -> pd.DataFrame:
        """Genera datos de prueba con n registros"""
        np.random.seed(42)
        fechas_inicio = pd.Timestamp('2024-01-01')
        fechas = [fechas_inicio + pd.Timedelta(days=np.random.randint(0, 365)) 
                  for _ in range(n_registros)]
        montos = np.random.normal(1000000, 300000, n_registros).round(2)
        montos = np.abs(montos)
        categorias = np.random.choice(['ventas', 'gastos'], n_registros, p=[0.7, 0.3])
        
        return pd.DataFrame({
            'fecha': fechas,
            'monto': montos,
            'categoria': categorias
        })


class TestPerformanceLoad:
    """Pruebas de carga con múltiples archivos secuenciales"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_multiple_uploads_sequential(self):
        """Prueba carga secuencial de múltiples archivos"""
        tiempos = []
        
        print("\n📊 Prueba de carga secuencial (5 archivos de 10,000 registros)")
        print("-" * 50)
        
        for i in range(5):
            df = self._generar_datos_prueba(10000)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                f.flush()
                
                with open(f.name, 'rb') as csv_file:
                    inicio = time.time()
                    response = client.post(
                        "/api/upload/",
                        files={"archivo": (f"archivo_{i}.csv", csv_file, "text/csv")}
                    )
                    tiempo = time.time() - inicio
                    tiempos.append(tiempo)
                    
                    print(f"   Archivo {i+1}: {tiempo:.4f} segundos")
                    
                    assert response.status_code == 200
            
            client.delete("/api/upload/")
        
        tiempo_promedio = sum(tiempos) / len(tiempos)
        print(f"\n   Tiempo promedio: {tiempo_promedio:.4f} segundos")
        
        assert tiempo_promedio < 1.0, f"Tiempo promedio de carga alto: {tiempo_promedio:.2f}s"
    
    def _generar_datos_prueba(self, n_registros: int) -> pd.DataFrame:
        """Genera datos de prueba con n registros"""
        np.random.seed(42)
        fechas_inicio = pd.Timestamp('2024-01-01')
        fechas = [fechas_inicio + pd.Timedelta(days=np.random.randint(0, 365)) 
                  for _ in range(n_registros)]
        montos = np.random.normal(1000000, 300000, n_registros).round(2)
        montos = np.abs(montos)
        categorias = np.random.choice(['ventas', 'gastos'], n_registros, p=[0.7, 0.3])
        
        return pd.DataFrame({
            'fecha': fechas,
            'monto': montos,
            'categoria': categorias
        })


# Para ejecutar solo las pruebas de rendimiento:
# pytest tests/performance/ -m performance -v

# Para ejecutar con benchmark (requiere pytest-benchmark):
# pytest tests/performance/test_performance.py --benchmark-only