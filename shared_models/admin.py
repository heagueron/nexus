from django.contrib import admin
from .models import Producto, Cliente

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('producto_id', 'nombre', 'codigo', 'marca', 'moneda', 'precio_venta', 'exento_iva', 'costo', 'stock', 'stock_bajo')
    list_filter = ('marca', 'unidad_medida', 'moneda', 'exento_iva')
    search_fields = ('nombre', 'codigo', 'marca', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
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
