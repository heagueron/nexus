from django.urls import path
from .views import (
    ProductoListCreateView, ProductoRetrieveUpdateDestroyView, ProductoStockBajoView,
    ClienteListCreateView, ClienteRetrieveUpdateDestroyView
)

urlpatterns = [
    # URLs para productos
    path('productos/', ProductoListCreateView.as_view(), name='producto-list-create'),
    path('productos/stock-bajo/', ProductoStockBajoView.as_view(), name='producto-stock-bajo'),
    path('productos/<int:pk>/', ProductoRetrieveUpdateDestroyView.as_view(), name='producto-detail'),

    # URLs para clientes
    path('clientes/', ClienteListCreateView.as_view(), name='cliente-list-create'),
    path('clientes/<int:pk>/', ClienteRetrieveUpdateDestroyView.as_view(), name='cliente-detail'),
]
