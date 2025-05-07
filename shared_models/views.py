from rest_framework import filters, generics
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import Producto, Cliente
from .serializers import ProductoSerializer, ClienteSerializer
from .filters import ProductoFilter, ClienteFilter

# Mixin para configuración común
class ProductoMixin:
    """
    Mixin con configuración común para las vistas de Producto.
    """
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductoFilter
    search_fields = ['nombre', 'codigo', 'marca', 'descripcion']
    ordering_fields = ['nombre', 'precio_venta', 'costo', 'stock']

# Vista para listar y crear productos
class ProductoListCreateView(ProductoMixin, generics.ListCreateAPIView):
    """
    API endpoint para listar y crear productos.

    list:
    Retorna una lista de todos los productos.

    create:
    Crea un nuevo producto.
    """
    pass

# Vista para recuperar, actualizar y eliminar un producto específico
class ProductoRetrieveUpdateDestroyView(ProductoMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint para recuperar, actualizar y eliminar un producto específico.

    retrieve:
    Retorna un producto específico.

    update:
    Actualiza un producto específico.

    partial_update:
    Actualiza parcialmente un producto específico.

    destroy:
    Elimina un producto específico.
    """
    pass

# Vista para productos con stock bajo
class ProductoStockBajoView(ProductoMixin, generics.ListAPIView):
    """
    API endpoint para listar productos con stock bajo.

    list:
    Retorna una lista de productos con stock bajo.
    """
    def get_queryset(self):
        """
        Filtra productos con stock menor o igual al nivel de alerta.
        """
        return Producto.objects.filter(stock__lte=models.F('alerta_stock'))


# Mixin para configuración común de Cliente
class ClienteMixin:
    """
    Mixin con configuración común para las vistas de Cliente.
    """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ClienteFilter
    search_fields = ['nombre', 'rif', 'email', 'direccion', 'nombre_contacto']
    ordering_fields = ['nombre', 'tipo', 'pais']


# Vista para listar y crear clientes
class ClienteListCreateView(ClienteMixin, generics.ListCreateAPIView):
    """
    API endpoint para listar y crear clientes.

    list:
    Retorna una lista de todos los clientes.

    create:
    Crea un nuevo cliente.
    """
    pass


# Vista para recuperar, actualizar y eliminar un cliente específico
class ClienteRetrieveUpdateDestroyView(ClienteMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint para recuperar, actualizar y eliminar un cliente específico.

    retrieve:
    Retorna un cliente específico.

    update:
    Actualiza un cliente específico.

    partial_update:
    Actualiza parcialmente un cliente específico.

    destroy:
    Elimina un cliente específico.
    """
    pass
