from sqlalchemy import Column, Integer, Numeric, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from Backend.database import Base


class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True)
    correlativo = Column(String(16), nullable=False, unique=True)
    fecha_emision = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)

    cliente_nombre = Column(String(200), nullable=False)
    cliente_rtn = Column(String(14))

    subtotal_exento = Column(Numeric(12, 2), default=0)
    subtotal_gravado_15 = Column(Numeric(12, 2), default=0)
    subtotal_gravado_18 = Column(Numeric(12, 2), default=0)
    isv_15 = Column(Numeric(12, 2), default=0)
    isv_18 = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)

    detalles = relationship("DetalleFactura", back_populates="factura")


class DetalleFactura(Base):
    __tablename__ = "detalle_facturas"

    id = Column(Integer, primary_key=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    cantidad = Column(Numeric(10), nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)
    tasa_isv = Column(String(10), default="15", nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    factura = relationship("Factura", back_populates="detalles")