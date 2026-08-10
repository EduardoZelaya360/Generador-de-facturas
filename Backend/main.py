import os
from pathlib import Path
from typing import List
import tempfile

from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session

from Backend.database import Base, engine, get_db
from Backend.models import Factura, DetalleFactura, LogoEmpresa
from Backend.pdf_generator import generar_pdf_factura

app = FastAPI(title="Generador de Facturas - Oracle")

Base.metadata.create_all(bind=engine)  # crea las tablas en Postgres si no existen

BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================
def obtener_logo_temp(rtn: str | None, nombre: str | None, db: Session) -> str:
    """Busca el logo en Oracle y devuelve la ruta de un archivo temporal si existe."""
    logo_db = None

    if rtn:
        logo_db = db.query(LogoEmpresa).filter(LogoEmpresa.rtn == rtn).first()
    elif nombre:
        logo_db = db.query(LogoEmpresa).filter(LogoEmpresa.nombre_empresa == nombre).first()

    if logo_db is not None and logo_db.logo is not None:
        temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".png", mode="wb")

        try:
            logo_raw = logo_db.logo
            if hasattr(logo_raw, "read"):
                logo_data: bytes = logo_raw.read()  # type: ignore[attr-defined]
            else:
                logo_data: bytes = logo_raw
            temp_logo.write(logo_data)
        except Exception as e:
            print(f"Error al leer BLOB de Oracle: {e}")
        finally:
            temp_logo.close()

        return temp_logo.name

    return ""

def eliminar_archivos_temporales(*rutas):
    """Elimina los archivos temporales pasados por parámetro de forma segura."""
    for ruta in rutas:
        if ruta and os.path.exists(ruta):
            try:
                os.unlink(ruta)
            except Exception as e:
                print(f"Error al eliminar archivo temporal {ruta}: {e}")

@app.get("/", response_class=HTMLResponse)
def cargar_formulario():
    """Carga y muestra el formulario HTML de la factura ubicado en Frontend/templates."""
    ruta_html = BASE_DIR / "Frontend" / "templates" / "Factura_form.html"

    if not ruta_html.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró el archivo HTML en la ruta esperada: {ruta_html}"
        )

    with open(ruta_html, "r", encoding="utf-8") as archivo:
        html_content = archivo.read()

    return HTMLResponse(content=html_content, status_code=200)


@app.post("/facturas")
def crear_y_generar_factura(
    background_tasks: BackgroundTasks,
    nombre_cliente: str = Form(...),
    rtn_cliente: str | None = Form(None),
    descripciones: List[str] = Form(...),
    cantidades: List[int] = Form(...),
    precios: List[float] = Form(...),
    tasas: List[str] = Form(...),
    logo: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    """Procesa los datos del formulario, los guarda en Oracle y devuelve el PDF generado."""
    try:
        items_validos = []
        subtotal_exento = 0.0
        subtotal_exonerado = 0.0
        subtotal_gravado_15 = 0.0
        subtotal_gravado_18 = 0.0
        isv_15 = 0.0
        isv_18 = 0.0

        for desc, cant, prec, tasa in zip(descripciones, cantidades, precios, tasas):
            if desc and desc.strip() and prec is not None and prec > 0:
                cant_val = cant if cant else 1
                subtotal_linea = cant_val * prec

                if tasa == "15":
                    subtotal_gravado_15 += subtotal_linea
                    isv_15 += subtotal_linea * 0.15
                elif tasa == "18":
                    subtotal_gravado_18 += subtotal_linea
                    isv_18 += subtotal_linea * 0.18
                elif tasa == "exonerado":
                    subtotal_exonerado += subtotal_linea
                else:
                    subtotal_exento += subtotal_linea

                items_validos.append({
                    "descripcion": desc.strip(),
                    "cantidad": cant_val,
                    "precio_unitario": prec,
                    "tasa_isv": tasa,
                    "subtotal": subtotal_linea
                })

        if not items_validos:
            raise HTTPException(
                status_code=400,
                detail="Debe ingresar al menos un ítem válido con descripción y precio."
            )

        total_general = subtotal_exento + subtotal_exonerado + subtotal_gravado_15 + subtotal_gravado_18 + isv_15 + isv_18

        total_reg = db.query(Factura).count() + 1
        correlativo_str = f"000-001-01-{total_reg:08d}"

        nueva_factura = Factura(
            correlativo=correlativo_str,
            cliente_nombre=nombre_cliente,
            cliente_rtn=rtn_cliente,
            subtotal_exento=subtotal_exento,
            subtotal_exonerado=subtotal_exonerado,
            subtotal_gravado_15=subtotal_gravado_15,
            subtotal_gravado_18=subtotal_gravado_18,
            isv_15=isv_15,
            isv_18=isv_18,
            total=total_general
        )
        db.add(nueva_factura)
        db.commit()
        db.refresh(nueva_factura)

        detalles_obj = []
        for item in items_validos:
            det = DetalleFactura(
                factura_id=nueva_factura.id,
                descripcion=item["descripcion"],
                cantidad=item["cantidad"],
                precio_unitario=item["precio_unitario"],
                tasa_isv=item["tasa_isv"],
                subtotal=item["subtotal"]
            )
            db.add(det)
            detalles_obj.append(det)
        db.commit()

        # =======================================================
        # LÓGICA DE MANEJO DE LOGOS (GUARDAR O REUTILIZAR)
        # =======================================================
        ruta_logo_temp = ""

        if logo and logo.filename:
            logo_bytes: bytes = logo.file.read()

            if rtn_cliente:
                logo_existente = db.query(LogoEmpresa).filter(LogoEmpresa.rtn == rtn_cliente).first()
            else:
                logo_existente = db.query(LogoEmpresa).filter(LogoEmpresa.nombre_empresa == nombre_cliente).first()

            if logo_existente is None:
                nuevo_logo = LogoEmpresa(
                    rtn=rtn_cliente,
                    nombre_empresa=nombre_cliente,
                    logo=logo_bytes
                )
                db.add(nuevo_logo)
            else:
                db.query(LogoEmpresa).filter(LogoEmpresa.id == logo_existente.id).update({
                    "logo": logo_bytes,
                    "nombre_empresa": nombre_cliente
                })

            db.commit()

            temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".png", mode="wb")
            temp_logo.write(logo_bytes)
            temp_logo.close()
            ruta_logo_temp = temp_logo.name

        else:
            ruta_logo_temp = obtener_logo_temp(rtn_cliente, nombre_cliente, db)

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_pdf.close()

        generar_pdf_factura(
            factura=nueva_factura,
            detalles=detalles_obj,
            ruta_logo=ruta_logo_temp,
            ruta_salida=temp_pdf.name
        )

        background_tasks.add_task(eliminar_archivos_temporales, temp_pdf.name, ruta_logo_temp)

        nombre_archivo = f"Factura_{correlativo_str.replace('/', '_').replace('-', '_')}.pdf"
        return FileResponse(
            temp_pdf.name,
            media_type="application/pdf",
            filename=nombre_archivo,
            content_disposition_type="attachment"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al procesar la factura: {str(e)}")


@app.get("/facturas/buscar/{rtn}")
def buscar_facturas_por_rtn(rtn: str, db: Session = Depends(get_db)):
    """Busca todas las facturas asociadas a un RTN específico."""
    facturas = db.query(Factura).filter(Factura.cliente_rtn == rtn).all()

    if not facturas:
        raise HTTPException(status_code=404, detail="No se encontraron facturas para este RTN.")

    resultados = []
    for f in facturas:
        resultados.append({
            "id": f.id,
            "correlativo": f.correlativo,
            "fecha": f.fecha_emision.strftime("%d-%m-%Y") if f.fecha_emision is not None else "N/D",
            "total": f.total
        })

    return {"cliente": facturas[0].cliente_nombre, "rtn": rtn, "facturas": resultados}


@app.get("/facturas/descargar/{factura_id}")
def descargar_factura_existente(
    factura_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Regenera y descarga el PDF de una factura ya existente en la base de datos."""
    factura = db.query(Factura).filter(Factura.id == factura_id).first()

    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    detalles = db.query(DetalleFactura).filter(DetalleFactura.factura_id == factura_id).all()

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.close()

    ruta_logo_temp = obtener_logo_temp(factura.cliente_rtn, factura.cliente_nombre, db)

    generar_pdf_factura(
        factura=factura,
        detalles=detalles,
        ruta_logo=ruta_logo_temp,
        ruta_salida=temp_pdf.name
    )

    background_tasks.add_task(eliminar_archivos_temporales, temp_pdf.name, ruta_logo_temp)

    nombre_archivo = f"Factura_Copia_{factura.correlativo.replace('/', '_').replace('-', '_')}.pdf"
    return FileResponse(
        temp_pdf.name,
        media_type="application/pdf",
        filename=nombre_archivo,
        content_disposition_type="attachment"
    )


# =====================================================================
# Búsqueda desde el HTML
# =====================================================================
@app.get("/buscar_factura")
def buscar_factura_html(
    numero_factura: str,
    background_tasks: BackgroundTasks,
    accion: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """Busca una factura desde el formulario HTML, la regenera y la muestra o descarga."""
    if numero_factura.isdigit():
        factura = db.query(Factura).filter(Factura.id == int(numero_factura)).first()
    else:
        factura = db.query(Factura).filter(Factura.correlativo == numero_factura).first()

    if not factura:
        raise HTTPException(
            status_code=404,
            detail=f"La factura '{numero_factura}' no existe en la base de datos."
        )

    detalles = db.query(DetalleFactura).filter(DetalleFactura.factura_id == factura.id).all()

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.close()

    ruta_logo_temp = obtener_logo_temp(factura.cliente_rtn, factura.cliente_nombre, db)

    generar_pdf_factura(
        factura=factura,
        detalles=detalles,
        ruta_logo=ruta_logo_temp,
        ruta_salida=temp_pdf.name
    )

    background_tasks.add_task(eliminar_archivos_temporales, temp_pdf.name, ruta_logo_temp)

    nombre_archivo = f"Factura_{factura.correlativo.replace('/', '_').replace('-', '_')}.pdf"
    disposition_type = "attachment" if accion == "descargar" else "inline"

    return FileResponse(
        temp_pdf.name,
        media_type="application/pdf",
        filename=nombre_archivo,
        content_disposition_type=disposition_type
    )