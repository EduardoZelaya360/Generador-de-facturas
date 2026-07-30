import re
from typing import Literal
from pydantic import BaseModel, field_validator


class ItemFacturaSchema(BaseModel):
    descripcion: str
    cantidad: int
    precio_unitario: float
    tasa_isv: Literal["exento", "15", "18"] = "15"

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return v

    @field_validator("precio_unitario")
    @classmethod
    def precio_no_negativo(cls, v):
        if v < 0:
            raise ValueError("El precio unitario no puede ser negativo")
        return v


class ClienteSchema(BaseModel):
    nombre: str
    rtn: str | None = None

    @field_validator("rtn")
    @classmethod
    def validar_rtn(cls, v):
        if v and not re.match(r"^\d{13,14}$", v):
            raise ValueError("El RTN debe tener 13 o 14 dígitos numéricos")
        return v


class FacturaFormSchema(BaseModel):
    cliente: ClienteSchema
    items: list[ItemFacturaSchema]

    @field_validator("items")
    @classmethod
    def al_menos_un_item(cls, v):
        if not v:
            raise ValueError("La factura debe tener al menos un ítem")
        return v