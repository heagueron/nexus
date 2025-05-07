import django_filters
from django.db import models
from .models import Producto

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
            'moneda': ['exact'],
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
