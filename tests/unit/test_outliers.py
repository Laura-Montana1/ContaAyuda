# tests/unit/test_outliers.py
import pandas as pd
from app.services.analysis_service import detectar_outliers

class TestDeteccionOutliers:
    """Pruebas unitarias para RF-07: Detección de valores anormales"""
    
    def test_detecta_pico_alto(self, sample_df_with_outliers):
        """Verifica que detecte valores anormalmente altos"""
        outliers = detectar_outliers(sample_df_with_outliers, umbral_std=2.0)
        
        assert outliers["total_outliers"] == 1
        assert outliers["valores_atipicos"][0]["tipo"] == "pico_alto"
        assert outliers["valores_atipicos"][0]["monto"] == 10000.0
    
    def test_sin_outliers(self):
        """Verifica que no detecte falsos positivos"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
            'monto': [1000.0, 1100.0, 1050.0, 1080.0],
            'categoria': ['ventas'] * 4
        })
        
        outliers = detectar_outliers(df, umbral_std=2.0)
        
        assert outliers["total_outliers"] == 0
    
    def test_umbral_configurable(self, sample_df_with_outliers):
        """Verifica que el umbral sea configurable"""
        # Con umbral bajo (1.0), detecta más outliers
        outliers_bajo = detectar_outliers(sample_df_with_outliers, umbral_std=1.0)
        
        # Con umbral alto (3.0), detecta menos
        outliers_alto = detectar_outliers(sample_df_with_outliers, umbral_std=3.0)
        
        assert outliers_alto["total_outliers"] <= outliers_bajo["total_outliers"]
    
    def test_incluye_criterio_estadistico(self, sample_df_with_outliers):
        """Verifica que incluya el criterio estadístico en la respuesta"""
        outliers = detectar_outliers(sample_df_with_outliers, umbral_std=2.0)
        
        assert "criterio" in outliers
        assert "media_diaria" in outliers["criterio"]
        assert "desviacion_estandar" in outliers["criterio"]
        assert "limite_superior" in outliers["criterio"]
        assert "limite_inferior" in outliers["criterio"]
    
    def test_detecta_pico_bajo(self):
        """Verifica que detecte valores anormalmente bajos"""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'monto': [2000.0, 2100.0, 50.0, 2050.0, 2000.0],
            'categoria': ['ventas'] * 5
        })
        
        outliers = detectar_outliers(df, umbral_std=2.0)
        
        assert outliers["total_outliers"] == 1
        assert outliers["valores_atipicos"][0]["tipo"] == "pico_bajo"