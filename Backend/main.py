from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from Backend.database import get_db
from Backend.models import Factura

app = FastAPI(title="Verificador de Registros - Oracle")

@app.get("/", response_class=HTMLResponse)
def verificar_registros(db: Session = Depends(get_db)):
    try:
        # 1. Verificar hora del servidor Oracle
        resultado_hora = db.execute(text("SELECT CURRENT_TIMESTAMP FROM DUAL")).fetchone()
        hora_oracle = resultado_hora[0] if resultado_hora else "Desconocida"
        
        # 2. Contar cuántas facturas hay registradas en la tabla
        total_facturas = db.query(Factura).count()
        
        # 3. Traer los últimos registros si los hay
        ultimas_facturas = db.query(Factura).order_by(Factura.id.desc()).limit(5).all()
        
        lista_html = ""
        if ultimas_facturas:
            for f in ultimas_facturas:
                lista_html += f"<li><b>Correlativo:</b> {f.correlativo} | <b>Cliente:</b> {f.cliente_nombre} | <b>Total:</b> L. {f.total}</li>"
        else:
            lista_html = "<li>No hay facturas registradas todavía en la base de datos.</li>"

        return f"""
        <html>
            <head><title>Estado de la Base de Datos</title></head>
            <body style="font-family: Arial; margin: 40px;">
                <h1 style="color: #2b7a78;">¡Conexión y consultas exitosas a Oracle!</h1>
                <p><strong>Hora del servidor Oracle:</strong> {hora_oracle}</p>
                <p><strong>Total de facturas en la base de datos:</strong> {total_facturas}</p>
                
                <h3>Últimos registros:</h3>
                <ul>
                    {lista_html}
                </ul>
            </body>
        </html>
        """
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar la base de datos: {str(e)}")