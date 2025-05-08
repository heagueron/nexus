from django.contrib import admin
from .models import Producto, Cliente, Moneda

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