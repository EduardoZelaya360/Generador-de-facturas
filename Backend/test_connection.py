"""
Prueba de conexión a Postgres (Neon), sin FastAPI de por medio.
Ejecutar desde la raíz del proyecto: python -m Backend.test_connection
"""

from sqlalchemy import text
from Backend.database import engine

try:
    with engine.connect() as conn:
        resultado = conn.execute(text("SELECT 1"))
        print("Conexión exitosa. Resultado:", resultado.fetchone())
except Exception as e:
    print("Error al conectar:", e)