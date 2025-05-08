from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Producto, Cliente, Moneda, Empresa

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('producto_id', 'nombre', 'codigo', 'marca', 'get_moneda_display', 'precio_venta', 'exento_iva', 'costo', 'stock', 'stock_bajo')
    list_filter = ('marca', 'unidad_medida', 'moneda', 'exento_iva')
    search_fields = ('nombre', 'codigo', 'marca', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    autocomplete_fields = ['moneda']  # Añadimos autocompletado para moneda
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'marca', 'descripcion', 'codigo')
        }),
        ('Información de Precios', {
            'fields': ('moneda', 'precio_venta', 'exento_iva', 'costo')
        }),
        ('Inventario', {
            'fields': ('unidad_medida', 'stock', 'alerta_stock')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def get_moneda_display(self, obj):
        """Muestra el nombre y símbolo de la moneda"""
        if obj.moneda:
            return f"{obj.moneda.nombre} ({obj.moneda.simbolo})"
        return "-"
    get_moneda_display.short_description = "Moneda"
    get_moneda_display.admin_order_field = 'moneda__nombre'

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente_id', 'tipo', 'rif', 'nombre', 'email', 'pais', 'telefono')
    list_filter = ('tipo', 'pais')
    search_fields = ('nombre', 'rif', 'email', 'direccion', 'nombre_contacto')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información Básica', {
            'fields': ('tipo', 'rif', 'nombre', 'email')
        }),
        ('Ubicación', {
            'fields': ('pais', 'direccion')
        }),
        ('Contacto', {
            'fields': ('telefono', 'nombre_contacto', 'telefono_contacto')
        }),
        ('Información Adicional', {
            'fields': ('comentario',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Moneda)
class MonedaAdmin(admin.ModelAdmin):
    list_display = ('moneda_id', 'nombre', 'simbolo', 'es_base', 'tasa_oficial', 'tasa_mercado', 'fecha_actualizacion')
    list_filter = ('es_base',)
    search_fields = ('nombre', 'simbolo')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering = ['-es_base', 'nombre']  # Ordenar con moneda base primero
    search_fields = ['nombre', 'simbolo']  # Habilitar búsqueda para autocompletado
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'simbolo', 'es_base')
        }),
        ('Tasas de Cambio', {
            'fields': ('tasa_oficial', 'tasa_mercado'),
            'description': 'Nota: Si la moneda es marcada como base, las tasas se establecerán automáticamente en 1.0'
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


class EmpresaAdmin(admin.ModelAdmin):
    """
    Admin personalizado para el modelo Empresa que implementa el patrón singleton.
    Previene la creación de múltiples instancias y proporciona una interfaz amigable.
    """
    list_display = ('nombre_legal', 'rif', 'ciudad', 'telefono', 'email')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_legal', 'nombre_comercial', 'rif', 'logo', 'es_activa')
        }),
        ('Contacto y Ubicación', {
            'fields': ('direccion_fiscal', 'ciudad', 'estado', 'pais', 'codigo_postal',
                      'telefono', 'email', 'sitio_web')
        }),
        ('Configuración Fiscal', {
            'fields': ('moneda_base', 'porcentaje_iva', 'aplica_retenciones')
        }),
        ('Configuración del Sistema', {
            'fields': ('formato_factura', 'formato_orden_compra', 'dias_alerta_vencimiento')
        }),
        ('Configuración Adicional', {
            'fields': ('configuracion_adicional',),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Previene la creación de múltiples instancias."""
        return not Empresa.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Previene la eliminación de la única instancia."""
        return False

    def changelist_view(self, request, extra_context=None):
        """
        Redirige a la página de edición de la única instancia si existe,
        o a la página de creación si no existe ninguna instancia.
        """
        try:
            # Obtener la única instancia
            empresa = Empresa.objects.get()
            return HttpResponseRedirect(
                reverse('admin:shared_models_empresa_change', args=[empresa.pk])
            )
        except Empresa.DoesNotExist:
            return HttpResponseRedirect(
                reverse('admin:shared_models_empresa_add')
            )
        except Empresa.MultipleObjectsReturned:
            # Si hay múltiples instancias (no debería ocurrir), mostrar la lista
            messages.warning(
                request,
                "Se encontraron múltiples instancias de Empresa. Esto no debería ocurrir."
            )
            return super().changelist_view(request, extra_context)


# Registrar el modelo Empresa con el admin personalizado
admin.site.register(Empresa, EmpresaAdmin)