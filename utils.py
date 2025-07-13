# utils.py
import re

def extraer_datos(mensaje):
    patron = r"(?:gast[ée]|gasto)\s+(\d+)\s+en\s+(.+)"
    coincidencia = re.search(patron, mensaje.lower())
    if coincidencia:
        monto = int(coincidencia.group(1))
        categoria = coincidencia.group(2).strip().capitalize()
        return monto, categoria
    return None, None
