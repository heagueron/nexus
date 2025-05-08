import django_filters
from django.db import models
from .models import Producto, Cliente, Moneda

class ProductoFilter(django_filters.FilterSet):
    """
    Filtro personalizado para el modelo Producto.
    """
    stock_bajo = django_filters.BooleanFilter(method='filter_stock_bajo')

    class Meta:
        model = Producto
        fields = {
            'marca': ['exact'],
            'unidad_medida': ['exact'],
            'moneda': ['exact'],  # Ahora filtra por ID de moneda
            'moneda__es_base': ['exact'],  # Filtrar por moneda base
            'moneda__nombre': ['exact', 'icontains'],  # Filtrar por nombre de moneda
            'exento_iva': ['exact'],
        }

    def filter_stock_bajo(self, queryset, name, value):
        """
        Filtra productos con stock bajo si value es True,
        o productos con stock normal si value es False.
        """
        if value:
            return queryset.filter(stock__lte=models.F('alerta_stock'))
        return queryset.filter(stock__gt=models.F('alerta_stock'))


class ClienteFilter(django_filters.FilterSet):
    """
    Filtro personalizado para el modelo Cliente.
    """
    class Meta:
        model = Cliente
        fields = {
            'tipo': ['exact'],
            'pais': ['exact'],
        }


class MonedaFilter(django_filters.FilterSet):
    """
    Filtro personalizado para el modelo Moneda.
    """
    class Meta:
        model = Moneda
        fields = {
            'nombre': ['exact', 'icontains'],
            'es_base': ['exact'],
            'simbolo': ['exact', 'icontains'],
        }