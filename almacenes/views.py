from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import Almacen, Ubicacion
from .serializers import (
    AlmacenSerializer, AlmacenListSerializer,
    UbicacionSerializer, UbicacionListSerializer, UbicacionDetailSerializer
)
from .filters import AlmacenFilter, UbicacionFilter


# Mixin para configuración común
class AlmacenMixin:
    """
    Mixin con configuración común para las vistas de Almacen.
    """
    queryset = Almacen.objects.all()
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlmacenFilter
    search_fields = ['nombre', 'ubicacion', 'descripcion', 'ciudad', 'pais', 'codigo_postal']
    ordering_fields = [
        'nombre', 'ubicacion', 'ciudad', 'tipo_almacen', 'activo',
        'capacidad_maxima', 'capacidad_utilizada', 'area_total',
        'fecha_apertura', 'fecha_cierre', 'fecha_creacion', 'fecha_actualizacion'
    ]


# Vista para listar y crear almacenes
class AlmacenListCreateView(AlmacenMixin, generics.ListCreateAPIView):
    """
    API endpoint para listar y crear almacenes.

    list:
    Retorna una lista de todos los almacenes.

    create:
    Crea un nuevo almacén.
    """
    def get_serializer_class(self):
        """
        Utiliza un serializador diferente para listar y crear.
        """
        if self.request.method == 'GET':
            return AlmacenListSerializer
        return AlmacenSerializer

    def perform_create(self, serializer):
        """
        Personaliza la creación de un almacén.
        """
        # Si no se proporciona un slug, se generará automáticamente en el método save()
        serializer.save()


# Vista para recuperar, actualizar y eliminar un almacén específico
class AlmacenRetrieveUpdateDestroyView(AlmacenMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint para recuperar, actualizar y eliminar un almacén específico.

    retrieve:
    Retorna un almacén específico.

    update:
    Actualiza un almacén específico.

    partial_update:
    Actualiza parcialmente un almacén específico.

    destroy:
    Elimina un almacén específico.
    """
    serializer_class = AlmacenSerializer
    lookup_field = 'slug'  # Usar slug en lugar de PK para URLs más amigables

    def get_object(self):
        """
        Recupera el objeto por slug o por ID.
        """
        queryset = self.get_queryset()

        # Verificar si estamos usando la URL con almacen_id
        if 'almacen_id' in self.kwargs:
            obj = get_object_or_404(queryset, almacen_id=self.kwargs['almacen_id'])
        else:
            # De lo contrario, usar el slug
            lookup_value = self.kwargs[self.lookup_field]
            obj = get_object_or_404(queryset, slug=lookup_value)

        # Verificar permisos
        self.check_object_permissions(self.request, obj)
        return obj


# Mixin para configuración común de Ubicacion
class UbicacionMixin:
    """
    Mixin con configuración común para las vistas de Ubicacion.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UbicacionFilter
    search_fields = ['codigo', 'nombre', 'descripcion', 'almacen__nombre']
    ordering_fields = [
        'codigo', 'nombre', 'almacen__nombre', 'tipo', 'capacidad',
        'nivel_jerarquia', 'activa', 'fecha_creacion', 'fecha_actualizacion'
    ]

    def get_queryset(self):
        """
        Retorna el queryset base con anotaciones útiles.
        """
        return Ubicacion.objects.select_related('almacen', 'padre').annotate(
            hijos_count=Count('hijos')
        )


# Vista para listar y crear ubicaciones
class UbicacionListCreateView(UbicacionMixin, generics.ListCreateAPIView):
    """
    API endpoint para listar y crear ubicaciones.

    list:
    Retorna una lista de todas las ubicaciones.

    create:
    Crea una nueva ubicación.
    """
    def get_serializer_class(self):
        """
        Utiliza un serializador diferente para listar y crear.
        """
        if self.request.method == 'GET':
            return UbicacionListSerializer
        return UbicacionSerializer

    def get_queryset(self):
        """
        Filtra las ubicaciones según los parámetros de la URL.
        """
        queryset = super().get_queryset()

        # Filtrar por almacén si se especifica en la URL
        almacen_id = self.request.query_params.get('almacen_id')
        if almacen_id:
            queryset = queryset.filter(almacen_id=almacen_id)

        # Filtrar por ubicaciones raíz (sin padre)
        solo_raices = self.request.query_params.get('solo_raices')
        if solo_raices and solo_raices.lower() in ('true', '1', 'yes'):
            queryset = queryset.filter(padre__isnull=True)

        # Filtrar por ubicaciones hijas de un padre específico
        padre_id = self.request.query_params.get('padre_id')
        if padre_id:
            queryset = queryset.filter(padre_id=padre_id)

        return queryset


# Vista para recuperar, actualizar y eliminar una ubicación específica
class UbicacionRetrieveUpdateDestroyView(UbicacionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint para recuperar, actualizar y eliminar una ubicación específica.

    retrieve:
    Retorna una ubicación específica.

    update:
    Actualiza una ubicación específica.

    partial_update:
    Actualiza parcialmente una ubicación específica.

    destroy:
    Elimina una ubicación específica.
    """
    lookup_field = 'codigo'

    def get_serializer_class(self):
        """
        Utiliza el serializador detallado para GET y el normal para PUT/PATCH.
        """
        if self.request.method == 'GET':
            return UbicacionDetailSerializer
        return UbicacionSerializer

    def get_object(self):
        """
        Recupera el objeto por código o por ID.
        """
        queryset = self.get_queryset()

        # Verificar si estamos usando la URL con ubicacion_id
        if 'ubicacion_id' in self.kwargs:
            obj = get_object_or_404(queryset, ubicacion_id=self.kwargs['ubicacion_id'])
        else:
            # Verificar si estamos buscando por código y almacén
            if 'codigo' in self.kwargs and 'almacen_id' in self.kwargs:
                obj = get_object_or_404(
                    queryset,
                    codigo=self.kwargs['codigo'],
                    almacen_id=self.kwargs['almacen_id']
                )
            else:
                # De lo contrario, buscar solo por código (asumiendo que es único)
                obj = get_object_or_404(queryset, codigo=self.kwargs['codigo'])

        # Verificar permisos
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_destroy(self, instance):
        """
        Verifica que la ubicación no tenga hijos antes de eliminarla.
        """
        if instance.hijos.exists():
            return Response(
                {"detail": "No se puede eliminar una ubicación que tiene ubicaciones hijas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
