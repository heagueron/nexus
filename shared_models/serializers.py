from rest_framework import serializers
from .models import Producto, Cliente

class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Producto.
    """
    margen = serializers.FloatField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'producto_id', 'nombre', 'marca', 'descripcion', 'codigo',
            'moneda', 'precio_venta', 'exento_iva', 'costo', 'unidad_medida',
            'stock', 'alerta_stock', 'margen', 'stock_bajo',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['producto_id', 'fecha_creacion', 'fecha_actualizacion']


class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Cliente.
    """
    class Meta:
        model = Cliente
        fields = [
            'cliente_id', 'tipo', 'rif', 'nombre', 'email', 'pais',
            'direccion', 'telefono', 'nombre_contacto', 'telefono_contacto',
            'comentario', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['cliente_id', 'fecha_creacion', 'fecha_actualizacion']
