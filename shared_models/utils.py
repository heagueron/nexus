"""
Utilidades para acceder a la configuración de la empresa y otras funcionalidades comunes.
"""
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject


def get_empresa():
    """
    Obtiene la instancia actual de Empresa.
    Utiliza el método get_current() del modelo Empresa.
    
    Returns:
        Empresa: La instancia actual de Empresa.
    """
    from .models import Empresa
    return Empresa.get_current()


# Objeto lazy que se evalúa solo cuando se accede a él
empresa = SimpleLazyObject(get_empresa)


def get_moneda_base():
    """
    Obtiene la moneda base del sistema.
    
    Returns:
        Moneda: La moneda base del sistema, o None si no existe.
    """
    from .models import Moneda
    return Moneda.get_moneda_base()


def get_porcentaje_iva():
    """
    Obtiene el porcentaje de IVA configurado en la empresa.
    
    Returns:
        Decimal: El porcentaje de IVA.
    """
    return empresa.porcentaje_iva


def get_formato_factura():
    """
    Obtiene el formato de factura configurado en la empresa.
    
    Returns:
        str: El formato de factura.
    """
    return empresa.formato_factura


def get_formato_orden_compra():
    """
    Obtiene el formato de orden de compra configurado en la empresa.
    
    Returns:
        str: El formato de orden de compra.
    """
    return empresa.formato_orden_compra


def format_numero_documento(formato, year, month, sequence):
    """
    Formatea un número de documento según el formato especificado.
    
    Args:
        formato (str): El formato a utilizar (ej: "FAC-{year}{month}-{sequence:04d}")
        year (int): El año
        month (int): El mes
        sequence (int): El número de secuencia
        
    Returns:
        str: El número de documento formateado
    """
    return formato.format(
        year=year,
        month=f"{month:02d}",
        sequence=sequence
    )


def clear_empresa_cache():
    """
    Limpia la caché de la empresa.
    Útil después de actualizaciones manuales en la base de datos.
    """
    cache.delete('empresa_singleton')
