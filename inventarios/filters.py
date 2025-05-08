import django_filters
from django.db.models import Q
from django.utils import timezone
from .models import Inventario, MovimientoInventario, EstadoLote, TipoMovimiento


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
