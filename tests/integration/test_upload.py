# tests/integration/test_upload.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestUploadIntegration:
    """Pruebas de integración para endpoint /api/upload"""
    
    def test_upload_valid_csv(self, sample_csv_valid):
        """Verifica carga exitosa de CSV válido"""
        with open(sample_csv_valid, 'rb') as f:
            response = client.post(
                "/api/upload/",
                files={"archivo": ("datos_validos.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["mensaje"] == "Archivo cargado y validado correctamente."
        assert "registros_cargados" in data
    
    def test_upload_valid_json(self, sample_json_valid):
        """Verifica carga exitosa de JSON válido"""
        with open(sample_json_valid, 'rb') as f:
            response = client.post(
                "/api/upload/",
                files={"archivo": ("datos_validos.json", f, "application/json")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["mensaje"] == "Archivo cargado y validado correctamente."
    
    def test_upload_empty_file_rejected(self):
        """Verifica rechazo de archivo vacío"""
        response = client.post(
            "/api/upload/",
            files={"archivo": ("vacio.csv", b"", "text/csv")}
        )
        
        assert response.status_code == 422
        assert "vacio" in str(response.json()).lower()
    
    def test_upload_invalid_format_rejected(self):
        """Verifica rechazo de formato no soportado"""
        response = client.post(
            "/api/upload/",
            files={"archivo": ("archivo.txt", b"fecha,monto,categoria", "text/plain")}
        )
        
        assert response.status_code >= 400
    
    def test_upload_file_too_large(self):
        """Verifica rechazo de archivo demasiado grande (>50MB)"""
        # Crear contenido de ~60MB
        large_content = b"x" * (60 * 1024 * 1024)
        
        response = client.post(
            "/api/upload/",
            files={"archivo": ("large.csv", large_content, "text/csv")}
        )
        
        assert response.status_code == 413
    
    def test_get_upload_status_after_upload(self, sample_csv_valid):
        """Verifica que después de cargar, el status indique datos presentes"""
        # Primero cargar
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        # Luego consultar status
        response = client.get("/api/upload/status")
        
        assert response.status_code == 200
        assert response.json()["cargado"] == True
    
    def test_delete_data(self, sample_csv_valid):
        """Verifica que se puedan limpiar los datos"""
        # Cargar datos
        with open(sample_csv_valid, 'rb') as f:
            client.post("/api/upload/", files={"archivo": ("datos.csv", f, "text/csv")})
        
        # Eliminar
        response = client.delete("/api/upload/")
        assert response.status_code == 200
        
        # Verificar que ya no hay datos
        status = client.get("/api/upload/status")
        assert status.json()["cargado"] == False