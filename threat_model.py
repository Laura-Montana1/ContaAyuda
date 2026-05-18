from pytm import *

tm = TM("Conta Ayuda - Threat Model")

tm.description = """
Sistema financiero para PYMES desarrollado con FastAPI.
Permite cargar archivos CSV/JSON y generar análisis financieros.
"""

# =========================
# ACTORES
# =========================

usuario = Actor("Usuario PYME")

frontend = ExternalEntity("Dashboard Frontend")

# =========================
# PROCESOS
# =========================

api = Process("API Conta Ayuda (FastAPI)")

api.description = """
Backend REST desarrollado con FastAPI.
Expone endpoints:
- /upload
- /analysis
- /report
"""

# =========================
# DATASTORE
# =========================

memoria = Datastore("Memoria Temporal")

memoria.description = """
Almacenamiento temporal de DataFrames en RAM.
"""

# =========================
# FLUJOS DE DATOS
# =========================

upload = Dataflow(
    usuario,
    api,
    "Carga CSV/JSON"
)

upload.protocol = "HTTP POST"

frontend_request = Dataflow(
    frontend,
    api,
    "Solicitudes de análisis"
)

frontend_request.protocol = "HTTP GET"

guardar_df = Dataflow(
    api,
    memoria,
    "Guardar DataFrame"
)

guardar_df.protocol = "RAM"

# =========================
# CONFIGURACIONES
# =========================

upload.isEncrypted = False
frontend_request.isEncrypted = False

# =========================
# PROCESAR MODELO
# =========================

tm.process()

# ===== FINDINGS PERSONALIZADOS =====

findings = [
    {
        "tipo": "Spoofing",
        "descripcion": "La API no implementa autenticación robusta.",
        "riesgo": "Alto"
    },
    {
        "tipo": "Tampering",
        "descripcion": "Los archivos CSV/JSON pueden ser modificados durante la transmisión HTTP.",
        "riesgo": "Alto"
    },
    {
        "tipo": "Information Disclosure",
        "descripcion": "Los datos financieros en memoria RAM no están cifrados.",
        "riesgo": "Medio"
    },
    {
        "tipo": "Denial of Service",
        "descripcion": "La API puede saturarse mediante múltiples cargas de archivos.",
        "riesgo": "Alto"
    },
    {
        "tipo": "Repudiation",
        "descripcion": "No existen logs de auditoría para rastrear acciones.",
        "riesgo": "Medio"
    }
]

print("\n===== AMENAZAS DETECTADAS =====\n")

for f in findings:
    print(f"[{f['tipo']}] Riesgo: {f['riesgo']}")
    print(f"Descripción: {f['descripcion']}\n")