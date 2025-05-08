"""
Script auxiliar para la migración de monedas.
Este script se utilizará en una migración personalizada para:
1. Crear las monedas necesarias
2. Convertir los valores de texto actuales a referencias
"""

def crear_monedas_iniciales(apps, schema_editor):
    """
    Crea las monedas iniciales necesarias para la migración.
    """
    Moneda = apps.get_model('shared_models', 'Moneda')
    
    # Crear moneda Bolívares (como moneda base)
    bolivares, created = Moneda.objects.get_or_create(
        nombre='Bolivares',
        defaults={
            'simbolo': 'Bs.',
            'es_base': True,
            'tasa_oficial': 1.0,
            'tasa_mercado': 1.0
        }
    )
    
    # Crear moneda Dólares
    dolares, created = Moneda.objects.get_or_create(
        nombre='USD',
        defaults={
            'simbolo': '$',
            'es_base': False,
            'tasa_oficial': 90.0,  # Valor ejemplo, debe ajustarse
            'tasa_mercado': 110.0   # Valor ejemplo, debe ajustarse
        }
    )
    
    return {
        'Bolivares': bolivares,
        'USD': dolares
    }

def actualizar_productos(apps, schema_editor):
    """
    Actualiza los productos para usar las nuevas monedas.
    """
    Producto = apps.get_model('shared_models', 'Producto')
    
    # Obtener las monedas creadas
    monedas = crear_monedas_iniciales(apps, schema_editor)
    
    # Actualizar productos con moneda 'Bolivares'
    Producto.objects.filter(moneda='Bolivares').update(moneda=monedas['Bolivares'])
    
    # Actualizar productos con moneda 'USD'
    Producto.objects.filter(moneda='USD').update(moneda=monedas['USD'])
