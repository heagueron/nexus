import django_filters
from django.db.models import Q
from .models import Almacen, Ubicacion, TipoAlmacen, UnidadMedidaCapacidad, TipoUbicacion


class AlmacenFilter(django_filters.FilterSet):
    """
    Filtros personalizados para el modelo Almacen.
    """
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    ubicacion = django_filters.CharFilter(lookup_expr='icontains')
    descripcion = django_filters.CharFilter(lookup_expr='icontains')
    ciudad = django_filters.CharFilter(lookup_expr='icontains')
    pais = django_filters.CharFilter(lookup_expr='icontains')
    codigo_postal = django_filters.CharFilter(lookup_expr='icontains')

    # Filtro para buscar en múltiples campos
    busqueda = django_filters.CharFilter(method='filtro_busqueda')

    # Filtros para rangos de capacidad
    capacidad_maxima_min = django_filters.NumberFilter(field_name='capacidad_maxima', lookup_expr='gte')
    capacidad_maxima_max = django_filters.NumberFilter(field_name='capacidad_maxima', lookup_expr='lte')
    capacidad_utilizada_min = django_filters.NumberFilter(field_name='capacidad_utilizada', lookup_expr='gte')
    capacidad_utilizada_max = django_filters.NumberFilter(field_name='capacidad_utilizada', lookup_expr='lte')
    area_total_min = django_filters.NumberFilter(field_name='area_total', lookup_expr='gte')
    area_total_max = django_filters.NumberFilter(field_name='area_total', lookup_expr='lte')

    # Filtros para fechas
    fecha_apertura_desde = django_filters.DateFilter(field_name='fecha_apertura', lookup_expr='gte')
    fecha_apertura_hasta = django_filters.DateFilter(field_name='fecha_apertura', lookup_expr='lte')
    fecha_cierre_desde = django_filters.DateFilter(field_name='fecha_cierre', lookup_expr='gte')
    fecha_cierre_hasta = django_filters.DateFilter(field_name='fecha_cierre', lookup_expr='lte')
    fecha_creacion_desde = django_filters.DateFilter(field_name='fecha_creacion', lookup_expr='gte')
    fecha_creacion_hasta = django_filters.DateFilter(field_name='fecha_creacion', lookup_expr='lte')

    # Filtros para campos booleanos
    activo = django_filters.BooleanFilter()

    # Filtros para campos de selección
    tipo_almacen = django_filters.ChoiceFilter(choices=TipoAlmacen.choices)
    unidad_medida_capacidad = django_filters.ChoiceFilter(choices=UnidadMedidaCapacidad.choices)

    def filtro_busqueda(self, queryset, _, value):
        """
        Filtro para buscar en múltiples campos.
        El parámetro '_' (antes 'name') no se utiliza pero es requerido por django-filter.
        """
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(ubicacion__icontains=value) |
            Q(descripcion__icontains=value) |
            Q(ciudad__icontains=value) |
            Q(codigo_postal__icontains=value) |
            Q(pais__icontains=value)
        )

    class Meta:
        model = Almacen
        fields = [
            'nombre', 'ubicacion', 'descripcion', 'ciudad', 'pais', 'codigo_postal',
            'tipo_almacen', 'activo', 'unidad_medida_capacidad', 'responsable'
        ]


class UbicacionFilter(django_filters.FilterSet):
    """
    Filtros personalizados para el modelo Ubicacion.
    """
    codigo = django_filters.CharFilter(lookup_expr='icontains')
    nombre = django_filters.CharFilter(lookup_expr='icontains')
    descripcion = django_filters.CharFilter(lookup_expr='icontains')

    # Filtros para relaciones
    almacen = django_filters.NumberFilter()
    almacen_nombre = django_filters.CharFilter(field_name='almacen__nombre', lookup_expr='icontains')
    padre = django_filters.NumberFilter(allow_null=True)
    sin_padre = django_filters.BooleanFilter(field_name='padre', lookup_expr='isnull')

    # Filtros para jerarquía
    nivel_jerarquia = django_filters.NumberFilter()
    nivel_jerarquia_min = django_filters.NumberFilter(field_name='nivel_jerarquia', lookup_expr='gte')
    nivel_jerarquia_max = django_filters.NumberFilter(field_name='nivel_jerarquia', lookup_expr='lte')

    # Filtros para capacidad
    capacidad_min = django_filters.NumberFilter(field_name='capacidad', lookup_expr='gte')
    capacidad_max = django_filters.NumberFilter(field_name='capacidad', lookup_expr='lte')

    # Filtros para campos booleanos
    activa = django_filters.BooleanFilter()

    # Filtros para campos de selección
    tipo = django_filters.ChoiceFilter(choices=TipoUbicacion.choices)
    unidad_medida_capacidad = django_filters.ChoiceFilter(choices=UnidadMedidaCapacidad.choices)

    # Filtro para buscar en múltiples campos
    busqueda = django_filters.CharFilter(method='filtro_busqueda')

    # Filtro para buscar por ruta
    ruta_contiene = django_filters.CharFilter(method='filtro_ruta')

    def filtro_busqueda(self, queryset, _, value):
        """
        Filtro para buscar en múltiples campos.
        """
        return queryset.filter(
            Q(codigo__icontains=value) |
            Q(nombre__icontains=value) |
            Q(descripcion__icontains=value) |
            Q(almacen__nombre__icontains=value)
        )

    def filtro_ruta(self, queryset, _, value):
        """
        Filtro para buscar ubicaciones cuya ruta completa contenga el valor.
        """
        # Primero obtenemos todas las ubicaciones
        ubicaciones = list(Ubicacion.objects.all())
        # Filtramos las que contienen el valor en su ruta
        ids = [u.pk for u in ubicaciones if value.lower() in u.ruta_completa.lower()]
        # Retornamos el queryset filtrado
        return queryset.filter(pk__in=ids)

    class Meta:
        model = Ubicacion
        fields = [
            'codigo', 'nombre', 'descripcion', 'almacen', 'padre',
            'tipo', 'activa', 'unidad_medida_capacidad'
        ]
