from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Almacen, Ubicacion, TipoUbicacion


class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo User (usado en el campo responsable).
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class AlmacenSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Almacen.
    """
    responsable = UserSerializer(read_only=True)
    responsable_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='responsable',
        write_only=True,
        required=False,
        allow_null=True
    )
    estado = serializers.CharField(read_only=True)
    porcentaje_ocupacion = serializers.FloatField(read_only=True)
    tipo_almacen_display = serializers.CharField(source='get_tipo_almacen_display', read_only=True)
    unidad_medida_capacidad_display = serializers.CharField(source='get_unidad_medida_capacidad_display', read_only=True)

    class Meta:
        model = Almacen
        fields = [
            # Campos básicos
            'almacen_id', 'nombre', 'slug', 'ubicacion', 'descripcion',
            # Contacto y responsable
            'responsable', 'responsable_id', 'email_contacto', 'telefono_contacto', 'horario_operacion',
            # Ubicación geográfica
            'ciudad', 'pais', 'codigo_postal', 'coordenadas_gps',
            # Capacidad y utilización
            'area_total', 'tipo_almacen', 'tipo_almacen_display',
            'capacidad_maxima', 'capacidad_utilizada', 'unidad_medida_capacidad', 'unidad_medida_capacidad_display',
            'porcentaje_ocupacion', 'estado',
            # Estado y operatividad
            'activo', 'fecha_apertura', 'fecha_cierre', 'notas_operativas',
            # Metadatos
            'metadatos',
            # Campos de sistema
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'almacen_id', 'fecha_creacion', 'fecha_actualizacion',
            'porcentaje_ocupacion', 'estado', 'tipo_almacen_display', 'unidad_medida_capacidad_display'
        ]


class AlmacenListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para listar almacenes.
    """
    estado = serializers.CharField(read_only=True)
    porcentaje_ocupacion = serializers.FloatField(read_only=True)
    tipo_almacen_display = serializers.CharField(source='get_tipo_almacen_display', read_only=True)
    ubicaciones_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Almacen
        fields = [
            'almacen_id', 'nombre', 'slug', 'ciudad', 'tipo_almacen_display',
            'activo', 'porcentaje_ocupacion', 'estado', 'ubicaciones_count'
        ]
        read_only_fields = fields


class UbicacionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Ubicacion.
    """
    almacen_nombre = serializers.CharField(source='almacen.nombre', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    unidad_medida_capacidad_display = serializers.CharField(source='get_unidad_medida_capacidad_display', read_only=True)
    ruta_completa = serializers.CharField(read_only=True)
    nivel_jerarquia = serializers.IntegerField(read_only=True)
    padre_codigo = serializers.CharField(source='padre.codigo', read_only=True, allow_null=True)
    padre_nombre = serializers.CharField(source='padre.nombre', read_only=True, allow_null=True)
    hijos_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Ubicacion
        fields = [
            # Campos básicos
            'ubicacion_id', 'codigo', 'nombre', 'tipo', 'tipo_display', 'activa', 'descripcion',
            # Jerarquía
            'almacen', 'almacen_nombre', 'padre', 'padre_codigo', 'padre_nombre',
            'ruta_completa', 'nivel_jerarquia', 'hijos_count',
            # Capacidad
            'capacidad', 'unidad_medida_capacidad', 'unidad_medida_capacidad_display',
            # Metadatos
            'metadatos',
            # Campos de sistema
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = [
            'ubicacion_id', 'fecha_creacion', 'fecha_actualizacion',
            'ruta_completa', 'nivel_jerarquia', 'hijos_count',
            'tipo_display', 'unidad_medida_capacidad_display',
            'almacen_nombre', 'padre_codigo', 'padre_nombre'
        ]


class UbicacionListSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para listar ubicaciones.
    """
    almacen_nombre = serializers.CharField(source='almacen.nombre', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    padre_codigo = serializers.CharField(source='padre.codigo', read_only=True, allow_null=True)
    hijos_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Ubicacion
        fields = [
            'ubicacion_id', 'codigo', 'nombre', 'almacen', 'almacen_nombre',
            'tipo', 'tipo_display', 'padre_codigo', 'activa', 'hijos_count'
        ]
        read_only_fields = fields


class UbicacionDetailSerializer(UbicacionSerializer):
    """
    Serializador para detalles de ubicación, incluyendo hijos directos.
    """
    hijos = serializers.SerializerMethodField()

    class Meta(UbicacionSerializer.Meta):
        fields = UbicacionSerializer.Meta.fields + ['hijos']

    def get_hijos(self, obj):
        """
        Obtiene los hijos directos de la ubicación.
        """
        hijos = obj.hijos.all()
        return UbicacionListSerializer(hijos, many=True, context=self.context).data
