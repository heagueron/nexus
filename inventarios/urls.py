from django.urls import path
from .views import (
    InventarioListCreateView, InventarioRetrieveUpdateDestroyView,
    InventarioAjusteView, InventarioReservaView, InventarioLiberacionView,
    MovimientoInventarioListView, MovimientoInventarioRetrieveView,
    ProductoAlimentoListCreateView, ProductoAlimentoRetrieveUpdateDestroyView,
    ProductoElectronicoListCreateView, ProductoElectronicoRetrieveUpdateDestroyView
)

urlpatterns = [
    # URLs para inventarios
    path('inventarios/', InventarioListCreateView.as_view(), name='inventario-list-create'),
    path('inventarios/<int:inventario_id>/', InventarioRetrieveUpdateDestroyView.as_view(), name='inventario-detail'),

    # URLs para operaciones de inventario
    path('inventarios/<int:inventario_id>/ajustar/', InventarioAjusteView.as_view(), name='inventario-ajustar'),
    path('inventarios/<int:inventario_id>/reservar/', InventarioReservaView.as_view(), name='inventario-reservar'),
    path('inventarios/<int:inventario_id>/liberar/', InventarioLiberacionView.as_view(), name='inventario-liberar'),

    # URLs para movimientos de inventario
    path('movimientos/', MovimientoInventarioListView.as_view(), name='movimiento-list'),
    path('movimientos/<int:movimiento_id>/', MovimientoInventarioRetrieveView.as_view(), name='movimiento-detail'),

    # URLs para productos alimenticios
    path('productos-alimentos/', ProductoAlimentoListCreateView.as_view(), name='producto-alimento-list-create'),
    path('productos-alimentos/<int:producto_id>/', ProductoAlimentoRetrieveUpdateDestroyView.as_view(), name='producto-alimento-detail'),

    # URLs para productos electrónicos
    path('productos-electronicos/', ProductoElectronicoListCreateView.as_view(), name='producto-electronico-list-create'),
    path('productos-electronicos/<int:producto_id>/', ProductoElectronicoRetrieveUpdateDestroyView.as_view(), name='producto-electronico-detail'),
]
