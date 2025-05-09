from rest_framework import serializers
from django.utils import timezone
from .models import (
    Inventario, MovimientoInventario, TipoMovimiento, EstadoLote,
    ProductoAlimento, ProductoElectronico,
    TipoConservacion, CategoriaAlimento, TipoElectronico
)
from shared_models.serializers import ProductoSerializer
from almacenes.serializers import AlmacenListSerializer, UbicacionListSerializer


class InventarioSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Inventario.
    """
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    almacen_nombre = serializers.CharField(source='almacen.nombre', read_only=True)
    ubicacion_codigo = serializers.CharField(source='ubicacion.codigo', read_only=True, allow_null=True)
    ubicacion_nombre = serializers.CharField(source='ubicacion.nombre', read_only=True, allow_null=True)
    estado_lote_display = serializers.CharField(source='get_estado_lote_display', read_only=True)
    cantidad_disponible = serializers.DecimalField(max_digits=15, decimal_places=3, read_only=True)
    valor_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, allow_null=True)
    dias_para_vencer = serializers.IntegerField(read_only=True, allow_null=True)
    esta_vencido = serializers.BooleanField(read_only=True)

    class Meta:
        model = Inventario
        fields = [
            'inventario_id', 'producto', 'producto_nombre', 'producto_codigo',
            'almacen', 'almacen_nombre', 'ubicacion', 'ubicacion_codigo', 'ubicacion_nombre',
            'lote', 'fecha_vencimiento', 'estado_lote', 'estado_lote_display',
            'cantidad', 'cantidad_reservada', 'cantidad_disponible',
            'costo_unitario', 'valor_total', 'dias_para_vencer', 'esta_vencido',
            'notas', 'metadatos', 'fecha_creacion', 'fecha_actualizacion', 'fecha_ultimo_movimiento'
        ]
        read_only_fields = [
            'inventario_id', 'fecha_creacion', 'fecha_actualizacion', 'fecha_ultimo_movimiento',
            'cantidad_disponible', 'valor_total', 'dias_para_vencer', 'esta_vencido'
        ]


class InventarioListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para listar inventarios.
    """
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    almacen_nombre = serializers.CharField(source='almacen.nombre', read_only=True)
    ubicacion_codigo = serializers.CharField(source='ubicacion.codigo', read_only=True, allow_null=True)
    estado_lote_display = serializers.CharField(source='get_estado_lote_display', read_only=True)
    cantidad_disponible = serializers.DecimalField(max_digits=15, decimal_places=3, read_only=True)

    class Meta:
        model = Inventario
        fields = [
            'inventario_id', 'producto_nombre', 'producto_codigo',
            'almacen_nombre', 'ubicacion_codigo', 'lote',
            'cantidad', 'cantidad_reservada', 'cantidad_disponible',
            'estado_lote_display', 'fecha_vencimiento'
        ]
        read_only_fields = fields


class InventarioDetailSerializer(InventarioSerializer):
    """
    Serializador para detalles de inventario, incluyendo información adicional.
    """
    producto = ProductoSerializer(read_only=True)
    almacen = AlmacenListSerializer(read_only=True)
    ubicacion = UbicacionListSerializer(read_only=True)
    movimientos_recientes = serializers.SerializerMethodField()

    class Meta(InventarioSerializer.Meta):
        fields = InventarioSerializer.Meta.fields + ['movimientos_recientes']

    def get_movimientos_recientes(self, obj):
        """
        Obtiene los movimientos más recientes del inventario.
        """
        movimientos = obj.movimientos.order_by('-fecha')[:5]
        return MovimientoInventarioListSerializer(movimientos, many=True, context=self.context).data


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo MovimientoInventario.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    producto_nombre = serializers.CharField(source='inventario.producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='inventario.producto.codigo', read_only=True)
    almacen_nombre = serializers.CharField(source='inventario.almacen.nombre', read_only=True)
    ubicacion_origen_codigo = serializers.CharField(source='ubicacion_origen.codigo', read_only=True, allow_null=True)
    ubicacion_destino_codigo = serializers.CharField(source='ubicacion_destino.codigo', read_only=True, allow_null=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'movimiento_id', 'inventario', 'tipo', 'tipo_display',
            'fecha', 'cantidad', 'es_incremento',
            'producto_nombre', 'producto_codigo', 'almacen_nombre',
            'ubicacion_origen', 'ubicacion_origen_codigo',
            'ubicacion_destino', 'ubicacion_destino_codigo',
            'referencia', 'codigo_seguimiento', 'usuario', 'notas'
        ]
        read_only_fields = [
            'movimiento_id', 'fecha', 'codigo_seguimiento',
            'tipo_display', 'producto_nombre', 'producto_codigo', 'almacen_nombre',
            'ubicacion_origen_codigo', 'ubicacion_destino_codigo'
        ]


class MovimientoInventarioListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para listar movimientos de inventario.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    producto_nombre = serializers.CharField(source='inventario.producto.nombre', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'movimiento_id', 'tipo', 'tipo_display', 'fecha',
            'cantidad', 'es_incremento', 'producto_nombre',
            'referencia', 'usuario'
        ]
        read_only_fields = fields


class AjusteInventarioSerializer(serializers.Serializer):
    """
    Serializador para realizar ajustes de inventario.
    """
    nueva_cantidad = serializers.DecimalField(
        max_digits=15,
        decimal_places=3,
        min_value=0,
        help_text="Nueva cantidad total del inventario"
    )
    motivo = serializers.CharField(
        max_length=255,
        help_text="Motivo del ajuste"
    )

    def validate_nueva_cantidad(self, value):
        """
        Valida que la nueva cantidad sea válida.
        """
        inventario = self.context.get('inventario')
        if not inventario:
            raise serializers.ValidationError("No se ha proporcionado un inventario.")

        if value < inventario.cantidad_reservada:
            raise serializers.ValidationError(
                "La nueva cantidad no puede ser menor que la cantidad reservada."
            )

        return value


class ReservaInventarioSerializer(serializers.Serializer):
    """
    Serializador para realizar reservas de inventario.
    """
    cantidad = serializers.DecimalField(
        max_digits=15,
        decimal_places=3,
        min_value=0.001,
        help_text="Cantidad a reservar"
    )
    referencia = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        help_text="Referencia opcional (ej: número de pedido)"
    )

    def validate_cantidad(self, value):
        """
        Valida que la cantidad a reservar sea válida.
        """
        inventario = self.context.get('inventario')
        if not inventario:
            raise serializers.ValidationError("No se ha proporcionado un inventario.")

        if value > inventario.cantidad_disponible:
            raise serializers.ValidationError(
                f"No hay suficiente stock disponible. Disponible: {inventario.cantidad_disponible}"
            )

        return value


class LiberacionInventarioSerializer(serializers.Serializer):
    """
    Serializador para liberar reservas de inventario.
    """
    cantidad = serializers.DecimalField(
        max_digits=15,
        decimal_places=3,
        min_value=0.001,
        help_text="Cantidad a liberar"
    )
    referencia = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        help_text="Referencia opcional (ej: número de pedido)"
    )

    def validate_cantidad(self, value):
        """
        Valida que la cantidad a liberar sea válida.
        """
        inventario = self.context.get('inventario')
        if not inventario:
            raise serializers.ValidationError("No se ha proporcionado un inventario.")

        if value > inventario.cantidad_reservada:
            raise serializers.ValidationError(
                f"La cantidad a liberar es mayor que la cantidad reservada. Reservada: {inventario.cantidad_reservada}"
            )

        return value


class ProductoAlimentoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo ProductoAlimento.
    """
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    tipo_conservacion_display = serializers.CharField(source='get_tipo_conservacion_display', read_only=True)
    moneda_nombre = serializers.CharField(source='moneda.nombre', read_only=True)
    moneda_simbolo = serializers.CharField(source='moneda.simbolo', read_only=True)
    margen = serializers.FloatField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)
    vida_util_total = serializers.IntegerField(read_only=True)
    porcentaje_vida_util_restante = serializers.FloatField(read_only=True)

    class Meta:
        model = ProductoAlimento
        fields = [
            'producto_id', 'nombre', 'marca', 'descripcion', 'codigo',
            'moneda', 'moneda_nombre', 'moneda_simbolo', 'precio_venta', 'exento_iva', 'costo',
            'unidad_medida', 'stock', 'alerta_stock', 'margen', 'stock_bajo',
            'fecha_elaboracion', 'fecha_expiracion', 'ingredientes', 'permiso_sanitario',
            'tipo_conservacion', 'tipo_conservacion_display', 'temperatura_minima', 'temperatura_maxima',
            'categoria', 'categoria_display', 'es_organico', 'contiene_alergenos', 'alergenos',
            'informacion_nutricional', 'pais_origen',
            'esta_vencido', 'dias_para_vencer', 'vida_util_total', 'porcentaje_vida_util_restante',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'producto_id', 'margen', 'stock_bajo', 'esta_vencido', 'dias_para_vencer',
            'vida_util_total', 'porcentaje_vida_util_restante',
            'fecha_creacion', 'fecha_actualizacion'
        ]


class ProductoAlimentoListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para listar productos alimenticios.
    """
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    tipo_conservacion_display = serializers.CharField(source='get_tipo_conservacion_display', read_only=True)
    moneda_simbolo = serializers.CharField(source='moneda.simbolo', read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductoAlimento
        fields = [
            'producto_id', 'nombre', 'codigo', 'precio_venta', 'moneda_simbolo',
            'stock', 'categoria_display', 'tipo_conservacion_display',
            'fecha_expiracion', 'dias_para_vencer', 'es_organico'
        ]
        read_only_fields = fields


class ProductoElectronicoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo ProductoElectronico.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    moneda_nombre = serializers.CharField(source='moneda.nombre', read_only=True)
    moneda_simbolo = serializers.CharField(source='moneda.simbolo', read_only=True)
    margen = serializers.FloatField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    garantia_valida_hasta = serializers.DateField(read_only=True)
    garantia_vigente = serializers.BooleanField(read_only=True)
    dias_restantes_garantia = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductoElectronico
        fields = [
            'producto_id', 'nombre', 'marca', 'descripcion', 'codigo',
            'moneda', 'moneda_nombre', 'moneda_simbolo', 'precio_venta', 'exento_iva', 'costo',
            'unidad_medida', 'stock', 'alerta_stock', 'margen', 'stock_bajo',
            'modelo', 'version_firmware', 'version_software', 'voltaje', 'garantia_meses',
            'tipo', 'tipo_display', 'numero_serie', 'fabricante', 'pais_origen',
            'potencia', 'consumo_energia', 'dimensiones', 'peso',
            'conectividad', 'certificaciones', 'es_reconstruido',
            'garantia_valida_hasta', 'garantia_vigente', 'dias_restantes_garantia',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'producto_id', 'margen', 'stock_bajo',
            'garantia_valida_hasta', 'garantia_vigente', 'dias_restantes_garantia',
            'fecha_creacion', 'fecha_actualizacion'
        ]


class ProductoElectronicoListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para listar productos electrónicos.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    moneda_simbolo = serializers.CharField(source='moneda.simbolo', read_only=True)
    garantia_vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductoElectronico
        fields = [
            'producto_id', 'nombre', 'codigo', 'precio_venta', 'moneda_simbolo',
            'stock', 'tipo_display', 'fabricante', 'modelo',
            'garantia_meses', 'garantia_vigente', 'es_reconstruido'
        ]
        read_only_fields = fields
