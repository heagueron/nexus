from rest_framework import serializers
from .models import Producto, Cliente, Moneda

class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Producto.
    """
    margen = serializers.FloatField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)

    # Añadimos campos anidados para mostrar información de la moneda
    moneda_nombre = serializers.CharField(source='moneda.nombre', read_only=True)
    moneda_simbolo = serializers.CharField(source='moneda.simbolo', read_only=True)

    class Meta:
        model = Producto
        fields = [
            'producto_id', 'nombre', 'marca', 'descripcion', 'codigo',
            'moneda', 'moneda_nombre', 'moneda_simbolo', 'precio_venta',
            'exento_iva', 'costo', 'unidad_medida',
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


class MonedaSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Moneda.
    """
    class Meta:
        model = Moneda
        fields = [
            'moneda_id', 'nombre', 'simbolo', 'es_base', 'tasa_oficial', 'tasa_mercado',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['moneda_id', 'fecha_creacion', 'fecha_actualizacion']

    def validate(self, data):
        """
        Valida que si es_base es True, no haya otra moneda base.
        """
        if data.get('es_base', False):
            # Si estamos actualizando, excluimos la instancia actual
            instance_id = self.instance.moneda_id if self.instance else None

            # Verificamos si ya existe otra moneda base
            if Moneda.objects.exclude(moneda_id=instance_id).filter(es_base=True).exists():
                raise serializers.ValidationError(
                    {"es_base": "Ya existe otra moneda marcada como base. Solo puede haber una moneda base en el sistema."}
                )

            # Si es moneda base, las tasas deben ser 1.0
            data['tasa_oficial'] = 1.0
            data['tasa_mercado'] = 1.0

        return data
