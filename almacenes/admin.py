from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Almacen, TipoAlmacen, UnidadMedidaCapacidad, Ubicacion, TipoUbicacion


@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('almacen_id', 'nombre', 'ciudad', 'tipo_almacen', 'activo', 'porcentaje_ocupacion_display', 'estado')
    list_filter = ('tipo_almacen', 'activo', 'pais', 'ciudad')
    search_fields = ('nombre', 'ubicacion', 'descripcion', 'ciudad', 'codigo_postal')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'porcentaje_ocupacion_display')
    prepopulated_fields = {'slug': ('nombre',)}

    def porcentaje_ocupacion_display(self, obj):
        return f"{obj.porcentaje_ocupacion}%"
    porcentaje_ocupacion_display.short_description = "Ocupación"

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'tipo_almacen', 'activo')
        }),
        ('Ubicación', {
            'fields': ('ubicacion', 'ciudad', 'pais', 'codigo_postal', 'coordenadas_gps')
        }),
        ('Contacto', {
            'fields': ('responsable', 'email_contacto', 'telefono_contacto', 'horario_operacion')
        }),
        ('Capacidad', {
            'fields': ('area_total', 'capacidad_maxima', 'capacidad_utilizada', 'unidad_medida_capacidad', 'porcentaje_ocupacion_display')
        }),
        ('Fechas', {
            'fields': ('fecha_apertura', 'fecha_cierre')
        }),
        ('Información Adicional', {
            'fields': ('descripcion', 'notas_operativas', 'metadatos')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


class UbicacionInline(admin.TabularInline):
    """
    Inline para mostrar las ubicaciones hijas de una ubicación.
    """
    model = Ubicacion
    fk_name = 'padre'
    extra = 1
    fields = ('codigo', 'nombre', 'tipo', 'capacidad', 'unidad_medida_capacidad', 'activa')
    verbose_name = "Ubicación hija"
    verbose_name_plural = "Ubicaciones hijas"


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    """
    Admin para el modelo Ubicacion.
    """
    list_display = ('codigo', 'nombre', 'almacen', 'tipo_display', 'padre_display', 'nivel_jerarquia', 'capacidad_display', 'activa')
    list_filter = ('almacen', 'tipo', 'activa')
    search_fields = ('codigo', 'nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'ruta_completa', 'nivel_jerarquia')
    inlines = [UbicacionInline]

    def tipo_display(self, obj):
        """Muestra el tipo de ubicación con un formato más amigable."""
        tipo_map = {
            'zona': '<span style="color: #1e88e5;">⬚</span> Zona',
            'pasillo': '<span style="color: #43a047;">▭</span> Pasillo',
            'estanteria': '<span style="color: #fb8c00;">▤</span> Estantería',
            'nivel': '<span style="color: #e53935;">▦</span> Nivel',
            'posicion': '<span style="color: #8e24aa;">▣</span> Posición',
            'otro': '<span style="color: #757575;">◯</span> Otro',
        }
        return format_html(tipo_map.get(obj.tipo, obj.get_tipo_display()))
    tipo_display.short_description = "Tipo"

    def padre_display(self, obj):
        """Muestra el padre de la ubicación, si existe."""
        if not obj.padre:
            return format_html('<span style="color: #757575;">—</span>')
        return format_html('<a href="{}">{}</a>',
                          f'../ubicacion/{obj.padre.pk}/change/',
                          f"{obj.padre.codigo} - {obj.padre.nombre}")
    padre_display.short_description = "Ubicación Padre"

    def capacidad_display(self, obj):
        """Muestra la capacidad con su unidad de medida."""
        if not obj.capacidad:
            return "—"
        return f"{obj.capacidad} {obj.get_unidad_medida_capacidad_display()}"
    capacidad_display.short_description = "Capacidad"

    def get_queryset(self, request):
        """Optimiza las consultas para el admin."""
        return super().get_queryset(request).select_related('almacen', 'padre')

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'tipo', 'activa')
        }),
        ('Jerarquía', {
            'fields': ('almacen', 'padre', 'ruta_completa', 'nivel_jerarquia')
        }),
        ('Capacidad', {
            'fields': ('capacidad', 'unidad_medida_capacidad')
        }),
        ('Información Adicional', {
            'fields': ('descripcion', 'metadatos')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
