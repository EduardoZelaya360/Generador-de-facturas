from sqlalchemy import Column, Integer, Numeric, String, TIMESTAMP, LargeBinary, ForeignKey, func
from sqlalchemy.orm import relationship
from Backend.database import Base


class Factura(Base):
    __tablename__ = "facturas"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    correlativo = Column("correlativo", String(20), nullable=False, unique=True)
    fecha_emision = Column("fecha_emision", TIMESTAMP, server_default=func.current_timestamp(), nullable=False)

    cliente_nombre = Column("cliente_nombre", String(200), nullable=False)
    cliente_rtn = Column("cliente_rtn", String(14))

    subtotal_exento = Column("subtotal_exento", Numeric(12, 2), default=0)
    subtotal_exonerado = Column("subtotal_exonerado", Numeric(12, 2), default=0) 
    subtotal_gravado_15 = Column("subtotal_gravado_15", Numeric(12, 2), default=0)
    subtotal_gravado_18 = Column("subtotal_gravado_18", Numeric(12, 2), default=0)
    isv_15 = Column("isv_15", Numeric(12, 2), default=0)
    isv_18 = Column("isv_18", Numeric(12, 2), default=0)
    total = Column("total", Numeric(12, 2), nullable=False)

    detalles = relationship("DetalleFactura", back_populates="factura", cascade="all, delete-orphan")


class DetalleFactura(Base):
    __tablename__ = "detalle_facturas"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    factura_id = Column("factura_id", Integer, ForeignKey("facturas.id"), nullable=False)
    descripcion = Column("descripcion", String(500), nullable=False)
    cantidad = Column("cantidad", Numeric(10), nullable=False)
    precio_unitario = Column("precio_unitario", Numeric(12, 2), nullable=False)
    tasa_isv = Column("tasa_isv", String(10), default="15", nullable=False)
    subtotal = Column("subtotal", Numeric(12, 2), nullable=False)

    factura = relationship("Factura", back_populates="detalles")


class LogoEmpresa(Base):
    __tablename__ = "logos_empresas"

    id = Column(Integer, primary_key=True, index=True)
    rtn = Column(String(14))
    nombre_empresa = Column(String(200))
    logo = Column(LargeBinary)  # LargeBinary es el equivalente a BLOB