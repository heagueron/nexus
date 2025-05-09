import django_filters
from django.db.models import Q, F
from django.utils import timezone
from .models import (
    Inventario, MovimientoInventario, EstadoLote, TipoMovimiento,
    ProductoAlimento, ProductoElectronico,
    TipoConservacion, CategoriaAlimento, TipoElectronico
)


class InventarioFilter(django_filters.FilterSet):
    """
    Filtros personalizados para el modelo Inventario.
    """
    # Filtros para producto
    producto = django_filters.NumberFilter()
    producto_nombre = django_filters.CharFilter(field_name='producto__nombre', lookup_expr='icontains')
    producto_codigo = django_filters.CharFilter(field_name='producto__codigo', lookup_expr='icontains')

    # Filtros para almacén y ubicación
    almacen = django_filters.NumberFilter()
    almacen_nombre = django_filters.CharFilter(field_name='almacen__nombre', lookup_expr='icontains')
    ubicacion = django_filters.NumberFilter(allow_null=True)
    ubicacion_codigo = django_filters.CharFilter(field_name='ubicacion__codigo', lookup_expr='icontains')
    sin_ubicacion = django_filters.BooleanFilter(field_name='ubicacion', lookup_expr='isnull')

    # Filtros para lote
    lote = django_filters.CharFilter(lookup_expr='icontains')
    estado_lote = django_filters.ChoiceFilter(choices=EstadoLote.choices)

    # Filtros para fechas
    fecha_vencimiento_desde = django_filters.DateFilter(field_name='fecha_vencimiento', lookup_expr='gte')
    fecha_vencimiento_hasta = django_filters.DateFilter(field_name='fecha_vencimiento', lookup_expr='lte')
    vencido = django_filters.BooleanFilter(method='filtro_vencido')
    por_vencer = django_filters.NumberFilter(method='filtro_por_vencer')

    # Filtros para cantidades
    cantidad_min = django_filters.NumberFilter(field_name='cantidad', lookup_expr='gte')
    cantidad_max = django_filters.NumberFilter(field_name='cantidad', lookup_expr='lte')
    disponible_min = django_filters.NumberFilter(method='filtro_disponible_min')
    disponible_max = django_filters.NumberFilter(method='filtro_disponible_max')
    con_stock = django_filters.BooleanFilter(method='filtro_con_stock')

    # Filtro para buscar en múltiples campos
    busqueda = django_filters.CharFilter(method='filtro_busqueda')

    def filtro_vencido(self, queryset, _, value):
        """
        Filtra inventarios vencidos o no vencidos.
        """
        hoy = timezone.now().date()
        if value:  # True: mostrar vencidos
            return queryset.filter(
                Q(fecha_vencimiento__lt=hoy) | Q(estado_lote=EstadoLote.VENCIDO)
            )
        else:  # False: mostrar no vencidos
            return queryset.filter(
                Q(fecha_vencimiento__gte=hoy) | Q(fecha_vencimiento__isnull=True)
            ).exclude(estado_lote=EstadoLote.VENCIDO)

    def filtro_por_vencer(self, queryset, _, value):
        """
        Filtra inventarios que vencen en los próximos N días.
        """
        if not value:
            return queryset

        hoy = timezone.now().date()
        limite = hoy + timezone.timedelta(days=value)

        return queryset.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=limite
        )

    def filtro_disponible_min(self, queryset, _, value):
        """
        Filtra inventarios con cantidad disponible mínima.
        """
        if not value:
            return queryset

        return queryset.filter(cantidad__gte=value + F('cantidad_reservada'))

    def filtro_disponible_max(self, queryset, _, value):
        """
        Filtra inventarios con cantidad disponible máxima.
        """
        if not value:
            return queryset

        return queryset.filter(cantidad__lte=value + F('cantidad_reservada'))

    def filtro_con_stock(self, queryset, _, value):
        """
        Filtra inventarios con o sin stock disponible.
        """
        if value:  # True: mostrar con stock
            return queryset.filter(cantidad__gt=F('cantidad_reservada'))
        else:  # False: mostrar sin stock
            return queryset.filter(cantidad__lte=F('cantidad_reservada'))

    def filtro_busqueda(self, queryset, _, value):
        """
        Filtro para buscar en múltiples campos.
        """
        return queryset.filter(
            Q(producto__nombre__icontains=value) |
            Q(producto__codigo__icontains=value) |
            Q(lote__icontains=value) |
            Q(almacen__nombre__icontains=value) |
            Q(ubicacion__codigo__icontains=value) |
            Q(notas__icontains=value)
        )

    class Meta:
        model = Inventario
        fields = [
            'producto', 'almacen', 'ubicacion', 'lote', 'estado_lote'
        ]


class MovimientoInventarioFilter(django_filters.FilterSet):
    """
    Filtros personalizados para el modelo MovimientoInventario.
    """
    # Filtros para inventario y producto
    inventario = django_filters.NumberFilter()
    producto = django_filters.NumberFilter(field_name='inventario__producto')
    producto_nombre = django_filters.CharFilter(field_name='inventario__producto__nombre', lookup_expr='icontains')
    producto_codigo = django_filters.CharFilter(field_name='inventario__producto__codigo', lookup_expr='icontains')

    # Filtros para almacén y ubicación
    almacen = django_filters.NumberFilter(field_name='inventario__almacen')
    almacen_nombre = django_filters.CharFilter(field_name='inventario__almacen__nombre', lookup_expr='icontains')
    ubicacion_origen = django_filters.NumberFilter()
    ubicacion_destino = django_filters.NumberFilter()

    # Filtros para tipo y referencia
    tipo = django_filters.ChoiceFilter(choices=TipoMovimiento.choices)
    referencia = django_filters.CharFilter(lookup_expr='icontains')
    codigo_seguimiento = django_filters.UUIDFilter()
    usuario = django_filters.CharFilter(lookup_expr='icontains')

    # Filtros para fechas
    fecha_desde = django_filters.DateTimeFilter(field_name='fecha', lookup_expr='gte')
    fecha_hasta = django_filters.DateTimeFilter(field_name='fecha', lookup_expr='lte')

    # Filtros para cantidades
    cantidad_min = django_filters.NumberFilter(field_name='cantidad', lookup_expr='gte')
    cantidad_max = django_filters.NumberFilter(field_name='cantidad', lookup_expr='lte')
    es_incremento = django_filters.BooleanFilter()

    # Filtro para buscar en múltiples campos
    busqueda = django_filters.CharFilter(method='filtro_busqueda')

    def filtro_busqueda(self, queryset, _, value):
        """
        Filtro para buscar en múltiples campos.
        """
        return queryset.filter(
            Q(inventario__producto__nombre__icontains=value) |
            Q(inventario__producto__codigo__icontains=value) |
            Q(referencia__icontains=value) |
            Q(notas__icontains=value) |
            Q(usuario__icontains=value)
        )

    class Meta:
        model = MovimientoInventario
        fields = [
            'inventario', 'tipo', 'es_incremento', 'referencia', 'usuario'
        ]


class ProductoAlimentoFilter(django_filters.FilterSet):
    """
    Filtros personalizados para el modelo ProductoAlimento.
    """
    # Filtros básicos de producto
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    codigo = django_filters.CharFilter(lookup_expr='icontains')
    marca = django_filters.CharFilter(lookup_expr='icontains')

    # Filtros específicos de alimentos
    categoria = django_filters.ChoiceFilter(choices=CategoriaAlimento.choices)
    tipo_conservacion = django_filters.ChoiceFilter(choices=TipoConservacion.choices)
    es_organico = django_filters.BooleanFilter()
    contiene_alergenos = django_filters.BooleanFilter()

    # Filtros de fechas
    fecha_elaboracion_desde = django_filters.DateFilter(field_name='fecha_elaboracion', lookup_expr='gte')
    fecha_elaboracion_hasta = django_filters.DateFilter(field_name='fecha_elaboracion', lookup_expr='lte')
    fecha_expiracion_desde = django_filters.DateFilter(field_name='fecha_expiracion', lookup_expr='gte')
    fecha_expiracion_hasta = django_filters.DateFilter(field_name='fecha_expiracion', lookup_expr='lte')
    vencido = django_filters.BooleanFilter(method='filtro_vencido')
    por_vencer = django_filters.NumberFilter(method='filtro_por_vencer')

    # Filtros de precios
    precio_min = django_filters.NumberFilter(field_name='precio_venta', lookup_expr='gte')
    precio_max = django_filters.NumberFilter(field_name='precio_venta', lookup_expr='lte')
    exento_iva = django_filters.BooleanFilter()

    # Filtros de stock
    stock_min = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_max = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    stock_bajo = django_filters.BooleanFilter(method='filtro_stock_bajo')

    # Filtro para buscar en múltiples campos
    busqueda = django_filters.CharFilter(method='filtro_busqueda')

    def filtro_vencido(self, queryset, _, value):
        """
        Filtra productos vencidos o no vencidos.
        """
        hoy = timezone.now().date()
        if value:  # True: mostrar vencidos
            return queryset.filter(fecha_expiracion__lt=hoy)
        else:  # False: mostrar no vencidos
            return queryset.filter(fecha_expiracion__gte=hoy)

    def filtro_por_vencer(self, queryset, _, value):
        """
        Filtra productos que vencen en los próximos N días.
        """
        if not value:
            return queryset

        hoy = timezone.now().date()
        limite = hoy + timezone.timedelta(days=value)

        return queryset.filter(
            fecha_expiracion__gte=hoy,
            fecha_expiracion__lte=limite
        )

    def filtro_stock_bajo(self, queryset, _, value):
        """
        Filtra productos con stock bajo o normal.
        """
        if value:  # True: mostrar con stock bajo
            return queryset.filter(stock__lte=F('alerta_stock'))
        else:  # False: mostrar con stock normal
            return queryset.filter(stock__gt=F('alerta_stock'))

    def filtro_busqueda(self, queryset, _, value):
        """
        Filtro para buscar en múltiples campos.
        """
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(codigo__icontains=value) |
            Q(marca__icontains=value) |
            Q(descripcion__icontains=value) |
            Q(ingredientes__icontains=value)
        )

    class Meta:
        model = ProductoAlimento
        fields = [
            'nombre', 'codigo', 'marca', 'categoria', 'tipo_conservacion',
            'es_organico', 'contiene_alergenos', 'exento_iva'
        ]


class ProductoElectronicoFilter(django_filters.FilterSet):
    """
    Filtros personalizados para el modelo ProductoElectronico.
    """
    # Filtros básicos de producto
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    codigo = django_filters.CharFilter(lookup_expr='icontains')
    marca = django_filters.CharFilter(lookup_expr='icontains')

    # Filtros específicos de electrónicos
    tipo = django_filters.ChoiceFilter(choices=TipoElectronico.choices)
    fabricante = django_filters.CharFilter(lookup_expr='icontains')
    modelo = django_filters.CharFilter(lookup_expr='icontains')
    numero_serie = django_filters.CharFilter(lookup_expr='icontains')
    es_reconstruido = django_filters.BooleanFilter()

    # Filtros de garantía
    garantia_meses_min = django_filters.NumberFilter(field_name='garantia_meses', lookup_expr='gte')
    garantia_meses_max = django_filters.NumberFilter(field_name='garantia_meses', lookup_expr='lte')
    garantia_vigente = django_filters.BooleanFilter(method='filtro_garantia_vigente')

    # Filtros de precios
    precio_min = django_filters.NumberFilter(field_name='precio_venta', lookup_expr='gte')
    precio_max = django_filters.NumberFilter(field_name='precio_venta', lookup_expr='lte')
    exento_iva = django_filters.BooleanFilter()

    # Filtros de stock
    stock_min = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_max = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    stock_bajo = django_filters.BooleanFilter(method='filtro_stock_bajo')

    # Filtro para buscar en múltiples campos
    busqueda = django_filters.CharFilter(method='filtro_busqueda')

    def filtro_garantia_vigente(self, queryset, _, value):
        """
        Filtra productos con garantía vigente o vencida.
        """
        hoy = timezone.now().date()

        # Calculamos la fecha de creación + garantía en meses (aproximado)
        if value:  # True: mostrar con garantía vigente
            return queryset.filter(
                fecha_creacion__gte=hoy - timezone.timedelta(days=F('garantia_meses') * 30)
            )
        else:  # False: mostrar con garantía vencida
            return queryset.filter(
                fecha_creacion__lt=hoy - timezone.timedelta(days=F('garantia_meses') * 30)
            )

    def filtro_stock_bajo(self, queryset, _, value):
        """
        Filtra productos con stock bajo o normal.
        """
        if value:  # True: mostrar con stock bajo
            return queryset.filter(stock__lte=F('alerta_stock'))
        else:  # False: mostrar con stock normal
            return queryset.filter(stock__gt=F('alerta_stock'))

    def filtro_busqueda(self, queryset, _, value):
        """
        Filtro para buscar en múltiples campos.
        """
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(codigo__icontains=value) |
            Q(marca__icontains=value) |
            Q(descripcion__icontains=value) |
            Q(modelo__icontains=value) |
            Q(fabricante__icontains=value) |
            Q(numero_serie__icontains=value)
        )

    class Meta:
        model = ProductoElectronico
        fields = [
            'nombre', 'codigo', 'marca', 'tipo', 'fabricante',
            'modelo', 'es_reconstruido', 'exento_iva'
        ]
