from django.urls import path
from .views import ProductoListCreateView, ProductoRetrieveUpdateDestroyView, ProductoStockBajoView

urlpatterns = [
    # URLs para productos
    path('productos/', ProductoListCreateView.as_view(), name='producto-list-create'),
    path('productos/stock-bajo/', ProductoStockBajoView.as_view(), name='producto-stock-bajo'),
    path('productos/<int:pk>/', ProductoRetrieveUpdateDestroyView.as_view(), name='producto-detail'),
]
