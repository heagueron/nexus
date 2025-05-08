from django.urls import path
from .views import (
    AlmacenListCreateView, AlmacenRetrieveUpdateDestroyView,
    UbicacionListCreateView, UbicacionRetrieveUpdateDestroyView
)

urlpatterns = [
    # URLs para almacenes
    path('almacenes/', AlmacenListCreateView.as_view(), name='almacen-list-create'),
    # URL para acceder por ID (debe ir antes que la URL con slug)
    path('almacenes/id/<int:almacen_id>/', AlmacenRetrieveUpdateDestroyView.as_view(), name='almacen-detail-by-id'),
    # URL principal usando slug
    path('almacenes/<slug:slug>/', AlmacenRetrieveUpdateDestroyView.as_view(), name='almacen-detail'),

    # URLs para ubicaciones
    path('ubicaciones/', UbicacionListCreateView.as_view(), name='ubicacion-list-create'),
    # URL para acceder por ID
    path('ubicaciones/id/<int:ubicacion_id>/', UbicacionRetrieveUpdateDestroyView.as_view(), name='ubicacion-detail-by-id'),
    # URL para acceder por código y almacén
    path('almacenes/<int:almacen_id>/ubicaciones/<str:codigo>/', UbicacionRetrieveUpdateDestroyView.as_view(), name='ubicacion-detail-by-almacen-codigo'),
    # URL principal usando código
    path('ubicaciones/<str:codigo>/', UbicacionRetrieveUpdateDestroyView.as_view(), name='ubicacion-detail'),

    # URLs para ubicaciones de un almacén específico
    path('almacenes/<int:almacen_id>/ubicaciones/', UbicacionListCreateView.as_view(), name='ubicacion-list-by-almacen'),
]
