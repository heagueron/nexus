from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import Producto
from .serializers import ProductoSerializer
from .filters import ProductoFilter

class ProductoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar productos.
    """
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductoFilter
    search_fields = ['nombre', 'codigo', 'marca', 'descripcion']
    ordering_fields = ['nombre', 'precio_venta', 'costo', 'stock']

    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """
        Retorna los productos con stock bajo.
        """
        productos = Producto.objects.filter(stock__lte=models.F('alerta_stock'))
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)
