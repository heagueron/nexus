from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from .models import (
    Inventario, MovimientoInventario,
    ProductoAlimento, ProductoElectronico
)
from .serializers import (
    InventarioSerializer, InventarioListSerializer, InventarioDetailSerializer,
    MovimientoInventarioSerializer, MovimientoInventarioListSerializer,
    AjusteInventarioSerializer, ReservaInventarioSerializer, LiberacionInventarioSerializer,
    ProductoAlimentoSerializer, ProductoAlimentoListSerializer,
    ProductoElectronicoSerializer, ProductoElectronicoListSerializer
)
from .filters import (
    InventarioFilter, MovimientoInventarioFilter,
    ProductoAlimentoFilter, ProductoElectronicoFilter
)


# Mixin para configuración común de Inventario
class InventarioMixin:
    """
    Mixin con configuración común para las vistas de Inventario.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InventarioFilter
    search_fields = ['producto__nombre', 'producto__codigo', 'lote', 'almacen__nombre', 'ubicacion__codigo']
    ordering_fields = [
        'producto__nombre', 'almacen__nombre', 'ubicacion__codigo',
        'cantidad', 'cantidad_reservada', 'fecha_vencimiento',
        'fecha_creacion', 'fecha_actualizacion', 'fecha_ultimo_movimiento'
    ]


# Vista para listar y crear inventarios
@extend_schema_view(
    list=extend_schema(
        summary="Listar inventarios",
        description="Retorna una lista paginada de todos los inventarios con información básica.",
        tags=["inventarios"],
        parameters=[
            OpenApiParameter(name="busqueda", description="Buscar en nombre, código, lote, etc.", required=False, type=str),
            OpenApiParameter(name="producto", description="Filtrar por ID de producto", required=False, type=int),
            OpenApiParameter(name="almacen", description="Filtrar por ID de almacén", required=False, type=int),
            OpenApiParameter(name="con_stock", description="Mostrar solo inventarios con stock disponible", required=False, type=bool),
        ]
    ),
    create=extend_schema(
        summary="Crear inventario",
        description="Crea un nuevo registro de inventario y genera automáticamente un movimiento de entrada.",
        tags=["inventarios"],
        examples=[
            OpenApiExample(
                "Ejemplo de creación",
                value={
                    "producto": 1,
                    "almacen": 1,
                    "ubicacion": 1,
                    "lote": "LOT-12345",
                    "cantidad": 100,
                    "costo_unitario": 25.50
                }
            )
        ]
    )
)
class InventarioListCreateView(InventarioMixin, generics.ListCreateAPIView):
    """
    API endpoint para listar y crear inventarios.
    """
    def get_serializer_class(self):
        """
        Utiliza un serializador diferente para listar y crear.
        """
        if self.request.method == 'GET':
            return InventarioListSerializer
        return InventarioSerializer

    def get_queryset(self):
        """
        Retorna el queryset base con anotaciones útiles.
        """
        return Inventario.objects.select_related('producto', 'almacen', 'ubicacion')

    def perform_create(self, serializer):
        """
        Guarda el inventario y registra el movimiento de entrada.
        """
        inventario = serializer.save(fecha_ultimo_movimiento=timezone.now())

        # Registrar el movimiento de entrada
        MovimientoInventario.objects.create(
            inventario=inventario,
            tipo='entrada',
            cantidad=inventario.cantidad,
            es_incremento=True,
            usuario=self.request.user.username if self.request.user.is_authenticated else None,
            notas="Creación inicial de inventario"
        )


# Vista para recuperar, actualizar y eliminar un inventario específico
@extend_schema_view(
    retrieve=extend_schema(
        summary="Obtener detalle de inventario",
        description="Retorna información detallada de un inventario específico, incluyendo movimientos recientes.",
        tags=["inventarios"],
    ),
    update=extend_schema(
        summary="Actualizar inventario",
        description="Actualiza un inventario existente. Si cambia la cantidad, genera automáticamente un movimiento de ajuste.",
        tags=["inventarios"],
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente inventario",
        description="Actualiza parcialmente un inventario existente. Si cambia la cantidad, genera automáticamente un movimiento de ajuste.",
        tags=["inventarios"],
    ),
    destroy=extend_schema(
        summary="Eliminar inventario",
        description="Elimina un inventario existente. Esta operación también actualiza el stock del producto.",
        tags=["inventarios"],
    )
)
class InventarioRetrieveUpdateDestroyView(InventarioMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint para recuperar, actualizar y eliminar un inventario específico.
    """
    lookup_field = 'inventario_id'

    def get_serializer_class(self):
        """
        Utiliza el serializador detallado para GET y el normal para PUT/PATCH.
        """
        if self.request.method == 'GET':
            return InventarioDetailSerializer
        return InventarioSerializer

    def get_queryset(self):
        """
        Retorna el queryset base con anotaciones útiles.
        """
        return Inventario.objects.select_related('producto', 'almacen', 'ubicacion')

    def perform_update(self, serializer):
        """
        Guarda el inventario y registra el movimiento si hay cambios en la cantidad.
        """
        # Obtener la instancia original
        original = self.get_object()
        original_cantidad = original.cantidad

        # Guardar los cambios
        inventario = serializer.save(fecha_ultimo_movimiento=timezone.now())

        # Verificar si cambió la cantidad
        if inventario.cantidad != original_cantidad:
            diferencia = inventario.cantidad - original_cantidad
            es_incremento = diferencia > 0

            # Registrar el movimiento
            MovimientoInventario.objects.create(
                inventario=inventario,
                tipo='ajuste',
                cantidad=abs(diferencia),
                es_incremento=es_incremento,
                usuario=self.request.user.username if self.request.user.is_authenticated else None,
                notas=f"Ajuste manual de cantidad: {original_cantidad} -> {inventario.cantidad}"
            )


# Vista para ajustar la cantidad de un inventario
@extend_schema(
    summary="Ajustar cantidad de inventario",
    description="Permite ajustar la cantidad total de un inventario y registra automáticamente un movimiento de ajuste.",
    tags=["inventarios"],
    request=AjusteInventarioSerializer,
    responses={
        200: OpenApiExample(
            "Éxito",
            value={"detail": "Ajuste realizado correctamente."}
        ),
        400: OpenApiExample(
            "Error",
            value={"detail": "La nueva cantidad es menor que la cantidad reservada."}
        ),
    }
)
class InventarioAjusteView(generics.GenericAPIView):
    """
    API endpoint para ajustar la cantidad de un inventario.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    serializer_class = AjusteInventarioSerializer

    def get_queryset(self):
        """
        Retorna el queryset base.
        """
        return Inventario.objects.all()

    def get_object(self):
        """
        Recupera el objeto por ID.
        """
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, inventario_id=self.kwargs['inventario_id'])
        self.check_object_permissions(self.request, obj)
        return obj

    def post(self, request, *args, **kwargs):
        """
        Ajusta la cantidad del inventario.
        """
        inventario = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'inventario': inventario})
        serializer.is_valid(raise_exception=True)

        # Realizar el ajuste
        nueva_cantidad = serializer.validated_data['nueva_cantidad']
        motivo = serializer.validated_data['motivo']

        try:
            inventario.ajustar(nueva_cantidad, motivo)
            return Response({'detail': 'Ajuste realizado correctamente.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Vista para reservar inventario
@extend_schema(
    summary="Reservar inventario",
    description="Permite reservar una cantidad del inventario para un pedido u otro propósito.",
    tags=["inventarios"],
    request=ReservaInventarioSerializer,
    responses={
        200: OpenApiExample(
            "Éxito",
            value={"detail": "Reserva realizada correctamente."}
        ),
        400: OpenApiExample(
            "Error",
            value={"detail": "No hay suficiente stock disponible para reservar."}
        ),
    }
)
class InventarioReservaView(generics.GenericAPIView):
    """
    API endpoint para reservar inventario.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    serializer_class = ReservaInventarioSerializer

    def get_queryset(self):
        """
        Retorna el queryset base.
        """
        return Inventario.objects.all()

    def get_object(self):
        """
        Recupera el objeto por ID.
        """
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, inventario_id=self.kwargs['inventario_id'])
        self.check_object_permissions(self.request, obj)
        return obj

    def post(self, request, *args, **kwargs):
        """
        Reserva una cantidad del inventario.
        """
        inventario = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'inventario': inventario})
        serializer.is_valid(raise_exception=True)

        # Realizar la reserva
        cantidad = serializer.validated_data['cantidad']
        referencia = serializer.validated_data.get('referencia')

        try:
            inventario.reservar(cantidad, referencia)
            return Response({'detail': 'Reserva realizada correctamente.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Vista para liberar inventario reservado
@extend_schema(
    summary="Liberar inventario reservado",
    description="Permite liberar una cantidad previamente reservada del inventario.",
    tags=["inventarios"],
    request=LiberacionInventarioSerializer,
    responses={
        200: OpenApiExample(
            "Éxito",
            value={"detail": "Liberación realizada correctamente."}
        ),
        400: OpenApiExample(
            "Error",
            value={"detail": "La cantidad a liberar es mayor que la cantidad reservada."}
        ),
    }
)
class InventarioLiberacionView(generics.GenericAPIView):
    """
    API endpoint para liberar inventario reservado.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    serializer_class = LiberacionInventarioSerializer

    def get_queryset(self):
        """
        Retorna el queryset base.
        """
        return Inventario.objects.all()

    def get_object(self):
        """
        Recupera el objeto por ID.
        """
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, inventario_id=self.kwargs['inventario_id'])
        self.check_object_permissions(self.request, obj)
        return obj

    def post(self, request, *args, **kwargs):
        """
        Libera una cantidad reservada del inventario.
        """
        inventario = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'inventario': inventario})
        serializer.is_valid(raise_exception=True)

        # Realizar la liberación
        cantidad = serializer.validated_data['cantidad']
        referencia = serializer.validated_data.get('referencia')

        try:
            inventario.liberar(cantidad, referencia)
            return Response({'detail': 'Liberación realizada correctamente.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Mixin para configuración común de MovimientoInventario
class MovimientoInventarioMixin:
    """
    Mixin con configuración común para las vistas de MovimientoInventario.
    """
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MovimientoInventarioFilter
    search_fields = ['inventario__producto__nombre', 'inventario__producto__codigo', 'referencia', 'notas', 'usuario']
    ordering_fields = ['fecha', 'tipo', 'cantidad', 'inventario__producto__nombre']


# Vista para listar movimientos de inventario
class MovimientoInventarioListView(MovimientoInventarioMixin, generics.ListAPIView):
    """
    API endpoint para listar movimientos de inventario.

    list:
    Retorna una lista de todos los movimientos de inventario.
    """
    serializer_class = MovimientoInventarioListSerializer

    def get_queryset(self):
        """
        Retorna el queryset base con relaciones.
        """
        return MovimientoInventario.objects.select_related(
            'inventario', 'inventario__producto', 'inventario__almacen',
            'ubicacion_origen', 'ubicacion_destino'
        )


# Vista para recuperar un movimiento de inventario específico
class MovimientoInventarioRetrieveView(MovimientoInventarioMixin, generics.RetrieveAPIView):
    """
    API endpoint para recuperar un movimiento de inventario específico.

    retrieve:
    Retorna un movimiento de inventario específico.
    """
    serializer_class = MovimientoInventarioSerializer
    lookup_field = 'movimiento_id'

    def get_queryset(self):
        """
        Retorna el queryset base con relaciones.
        """
        return MovimientoInventario.objects.select_related(
            'inventario', 'inventario__producto', 'inventario__almacen',
            'ubicacion_origen', 'ubicacion_destino'
        )


# Vistas para ProductoAlimento

@extend_schema_view(
    list=extend_schema(
        summary="Listar productos alimenticios",
        description="Retorna una lista paginada de todos los productos alimenticios.",
        tags=["productos-alimentos"],
    ),
    create=extend_schema(
        summary="Crear producto alimenticio",
        description="Crea un nuevo producto alimenticio.",
        tags=["productos-alimentos"],
    )
)
class ProductoAlimentoListCreateView(generics.ListCreateAPIView):
    """
    API endpoint para listar y crear productos alimenticios.
    """
    queryset = ProductoAlimento.objects.all()
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductoAlimentoFilter
    search_fields = ['nombre', 'codigo', 'marca', 'descripcion', 'ingredientes']
    ordering_fields = ['nombre', 'codigo', 'fecha_expiracion', 'categoria']

    def get_serializer_class(self):
        """
        Utiliza un serializador diferente para listar y crear.
        """
        if self.request.method == 'GET':
            return ProductoAlimentoListSerializer
        return ProductoAlimentoSerializer


@extend_schema_view(
    retrieve=extend_schema(
        summary="Obtener detalle de producto alimenticio",
        description="Retorna información detallada de un producto alimenticio específico.",
        tags=["productos-alimentos"],
    ),
    update=extend_schema(
        summary="Actualizar producto alimenticio",
        description="Actualiza un producto alimenticio existente.",
        tags=["productos-alimentos"],
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente producto alimenticio",
        description="Actualiza parcialmente un producto alimenticio existente.",
        tags=["productos-alimentos"],
    ),
    destroy=extend_schema(
        summary="Eliminar producto alimenticio",
        description="Elimina un producto alimenticio existente.",
        tags=["productos-alimentos"],
    )
)
class ProductoAlimentoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint para recuperar, actualizar y eliminar un producto alimenticio específico.
    """
    queryset = ProductoAlimento.objects.all()
    serializer_class = ProductoAlimentoSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    lookup_field = 'producto_id'


# Vistas para ProductoElectronico

@extend_schema_view(
    list=extend_schema(
        summary="Listar productos electrónicos",
        description="Retorna una lista paginada de todos los productos electrónicos.",
        tags=["productos-electronicos"],
    ),
    create=extend_schema(
        summary="Crear producto electrónico",
        description="Crea un nuevo producto electrónico.",
        tags=["productos-electronicos"],
    )
)
class ProductoElectronicoListCreateView(generics.ListCreateAPIView):
    """
    API endpoint para listar y crear productos electrónicos.
    """
    queryset = ProductoElectronico.objects.all()
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductoElectronicoFilter
    search_fields = ['nombre', 'codigo', 'marca', 'descripcion', 'modelo', 'fabricante']
    ordering_fields = ['nombre', 'codigo', 'fabricante', 'tipo']

    def get_serializer_class(self):
        """
        Utiliza un serializador diferente para listar y crear.
        """
        if self.request.method == 'GET':
            return ProductoElectronicoListSerializer
        return ProductoElectronicoSerializer


@extend_schema_view(
    retrieve=extend_schema(
        summary="Obtener detalle de producto electrónico",
        description="Retorna información detallada de un producto electrónico específico.",
        tags=["productos-electronicos"],
    ),
    update=extend_schema(
        summary="Actualizar producto electrónico",
        description="Actualiza un producto electrónico existente.",
        tags=["productos-electronicos"],
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente producto electrónico",
        description="Actualiza parcialmente un producto electrónico existente.",
        tags=["productos-electronicos"],
    ),
    destroy=extend_schema(
        summary="Eliminar producto electrónico",
        description="Elimina un producto electrónico existente.",
        tags=["productos-electronicos"],
    )
)
class ProductoElectronicoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint para recuperar, actualizar y eliminar un producto electrónico específico.
    """
    queryset = ProductoElectronico.objects.all()
    serializer_class = ProductoElectronicoSerializer
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación (solo para desarrollo)
    lookup_field = 'producto_id'