import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generar_pdf_factura(factura, detalles, ruta_logo: str, ruta_salida: str):
    doc = SimpleDocTemplate(
        ruta_salida, 
        pagesize=letter, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=30, 
        bottomMargin=30,
        title=f"Factura - {factura.correlativo}",
        author="Generador de Facturas - Honduras"
    )
    
    story = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'TituloFactura',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2b7a78'),
        alignment=1 # Centrado
    )
    
    texto_normal = styles['Normal']

    # 1. Cabecera con Logo y Datos de la Factura
    header_data = []
    
    # Manejo seguro de la fecha (por si viene de la BD como objeto o nula)
    fecha_str = factura.fecha_emision.strftime("%d-%m-%Y") if factura.fecha_emision else "N/D"
    
    if ruta_logo and os.path.exists(ruta_logo):
        try:
            img = Image(ruta_logo, width=80, height=40)
            header_data.append([img, Paragraph(f"<b>FACTURA</b><br/>Correlativo: {factura.correlativo}<br/>Fecha: {fecha_str}", texto_normal)])
        except:
            header_data.append([Paragraph("<b>LOGO</b>", texto_normal), Paragraph(f"<b>FACTURA</b><br/>Correlativo: {factura.correlativo}", texto_normal)])
    else:
        header_data.append([Paragraph("<b>EMPRESA</b>", texto_normal), Paragraph(f"<b>FACTURA</b><br/>Correlativo: {factura.correlativo}<br/>Fecha: {fecha_str}", texto_normal)])

    t_header = Table(header_data, colWidths=[90, 450])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(t_header)
    story.append(Spacer(1, 15))

    # 2. Datos del Cliente
    cliente_data = [
        [Paragraph(f"<b>Cliente:</b> {factura.cliente_nombre}", texto_normal)],
        [Paragraph(f"<b>RTN:</b> {factura.cliente_rtn or 'N/D'}", texto_normal)]
    ]
    t_cliente = Table(cliente_data, colWidths=[540])
    t_cliente.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f4f4f4'))
    ]))
    
    story.append(t_cliente)
    story.append(Spacer(1, 15))

    # 3. Tabla de Ítems
    tabla_items_data = [["Descripción", "Cant.", "Precio Unit.", "Tasa", "Subtotal"]]
    
    for d in detalles:
        tabla_items_data.append([
            d.descripcion,
            str(d.cantidad),
            f"L. {d.precio_unitario:.2f}",
            str(d.tasa_isv),
            f"L. {d.subtotal:.2f}"
        ])

    t_items = Table(tabla_items_data, colWidths=[220, 60, 90, 70, 100])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2b7a78')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')])
    ]))
    
    story.append(t_items)
    story.append(Spacer(1, 15))

    # 4. Totales de la Factura (Impuestos de Honduras)
    totales_data = [
        ["Subtotal Exento:", f"L. {factura.subtotal_exento:.2f}"],
        ["Subtotal Exonerado:", f"L. {factura.subtotal_exonerado:.2f}"],
        ["Subtotal Gravado 15%:", f"L. {factura.subtotal_gravado_15:.2f}"],
        ["Subtotal Gravado 18%:", f"L. {factura.subtotal_gravado_18:.2f}"],
        ["ISV 15%:", f"L. {factura.isv_15:.2f}"],
        ["ISV 18%:", f"L. {factura.isv_18:.2f}"],
        ["TOTAL A PAGAR:", f"L. {factura.total:.2f}"]
    ]
    
    t_totales = Table(totales_data, colWidths=[400, 140])
    t_totales.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e2e2e2')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    
    story.append(t_totales)

    # Construir PDF
    doc.build(story)