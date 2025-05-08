from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Sum, F
from .models import Inventario, MovimientoInventario, EstadoLote


class MovimientoInventarioInline(admin.TabularInline):
    """
    Inline para mostrar los movimientos de un inventario.
    """
    model = MovimientoInventario
    extra = 0
    fields = ('tipo', 'fecha', 'cantidad', 'es_incremento', 'referencia', 'notas')
    readonly_fields = ('fecha',)
    can_delete = False
    max_num = 10
    verbose_name = _("Movimiento")
    verbose_name_plural = _("Últimos 10 Movimientos")
    
    def get_queryset(self, request):
        """
        Limita los movimientos a los 10 más recientes.
        """
        queryset = super().get_queryset(request)
        return queryset.order_by('-fecha')[:10]


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    """
    Admin para el modelo Inventario.
    """
    list_display = ('producto_display', 'almacen', 'ubicacion_display', 'lote_display', 
                    'cantidad_display', 'cantidad_reservada_display', 'cantidad_disponible_display', 
                    'estado_lote_display', 'dias_para_vencer_display')
    list_filter = ('almacen', 'estado_lote', 'producto__nombre', 'ubicacion__codigo')
    search_fields = ('producto__nombre', 'producto__codigo', 'lote', 'ubicacion__codigo')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_ultimo_movimiento', 
                       'cantidad_disponible', 'valor_total', 'dias_para_vencer')
    inlines = [MovimientoInventarioInline]
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('producto', 'almacen', 'ubicacion')
        }),
        (_('Información de Lote'), {
            'fields': ('lote', 'fecha_vencimiento', 'estado_lote', 'dias_para_vencer')
        }),
        (_('Cantidades'), {
            'fields': ('cantidad', 'cantidad_reservada', 'cantidad_disponible')
        }),
        (_('Información Financiera'), {
            'fields': ('costo_unitario', 'valor_total')
        }),
        (_('Información Adicional'), {
            'fields': ('notas', 'metadatos')
        }),
        (_('Información del Sistema'), {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'fecha_ultimo_movimiento'),
            'classes': ('collapse',)
        }),
    )
    
    def producto_display(self, obj):
        """Muestra el producto con formato."""
        return format_html('<strong>{}</strong> <span style="color: #888;">({})</span>', 
                          obj.producto.nombre, obj.producto.codigo)
    producto_display.short_description = _("Producto")
    
    def ubicacion_display(self, obj):
        """Muestra la ubicación con formato."""
        if not obj.ubicacion:
            return "—"
        return format_html('<span title="{}">{}</span>', 
                          obj.ubicacion.ruta_completa, obj.ubicacion.codigo)
    ubicacion_display.short_description = _("Ubicación")
    
    def lote_display(self, obj):
        """Muestra el lote con formato."""
        if not obj.lote:
            return "—"
        return obj.lote
    lote_display.short_description = _("Lote")
    
    def cantidad_display(self, obj):
        """Muestra la cantidad con formato."""
        return format_html('<span style="font-weight: bold;">{:.3f}</span>', obj.cantidad)
    cantidad_display.short_description = _("Cantidad")
    
    def cantidad_reservada_display(self, obj):
        """Muestra la cantidad reservada con formato."""
        if obj.cantidad_reservada == 0:
            return "0"
        return format_html('<span style="color: #e67e22;">{:.3f}</span>', obj.cantidad_reservada)
    cantidad_reservada_display.short_description = _("Reservada")
    
    def cantidad_disponible_display(self, obj):
        """Muestra la cantidad disponible con formato."""
        if obj.cantidad_disponible <= 0:
            return format_html('<span style="color: #e74c3c;">0</span>')
        return format_html('<span style="color: #27ae60;">{:.3f}</span>', obj.cantidad_disponible)
    cantidad_disponible_display.short_description = _("Disponible")
    
    def estado_lote_display(self, obj):
        """Muestra el estado del lote con formato."""
        color_map = {
            'disponible': '#27ae60',  # Verde
            'cuarentena': '#f39c12',  # Naranja
            'bloqueado': '#e74c3c',   # Rojo
            'vencido': '#7f8c8d',     # Gris
            'agotado': '#95a5a6',     # Gris claro
        }
        color = color_map.get(obj.estado_lote, '#3498db')
        return format_html('<span style="color: {};">{}</span>', 
                          color, obj.get_estado_lote_display())
    estado_lote_display.short_description = _("Estado")
    
    def dias_para_vencer_display(self, obj):
        """Muestra los días para vencer con formato."""
        if not obj.fecha_vencimiento:
            return "—"
        
        dias = obj.dias_para_vencer
        if dias == 0:
            return format_html('<span style="color: #e74c3c;">Vencido</span>')
        elif dias <= 30:
            return format_html('<span style="color: #e67e22;">{} días</span>', dias)
        else:
            return format_html('{} días', dias)
    dias_para_vencer_display.short_description = _("Días para vencer")


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    """
    Admin para el modelo MovimientoInventario.
    """
    list_display = ('fecha', 'tipo_display', 'producto_display', 'almacen_display', 
                    'cantidad_display', 'referencia', 'usuario')
    list_filter = ('tipo', 'fecha', 'inventario__almacen', 'inventario__producto')
    search_fields = ('inventario__producto__nombre', 'inventario__producto__codigo', 
                     'referencia', 'notas', 'usuario')
    readonly_fields = ('fecha', 'codigo_seguimiento')
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('inventario', 'tipo', 'fecha', 'cantidad', 'es_incremento')
        }),
        (_('Información de Traslado'), {
            'fields': ('ubicacion_origen', 'ubicacion_destino'),
            'classes': ('collapse',)
        }),
        (_('Información Adicional'), {
            'fields': ('referencia', 'codigo_seguimiento', 'usuario', 'notas')
        }),
    )
    
    def tipo_display(self, obj):
        """Muestra el tipo de movimiento con formato."""
        color_map = {
            'entrada': '#27ae60',     # Verde
            'salida': '#e74c3c',      # Rojo
            'traslado': '#3498db',    # Azul
            'ajuste': '#f39c12',      # Naranja
            'reserva': '#9b59b6',     # Morado
            'liberacion': '#2ecc71',  # Verde claro
        }
        color = color_map.get(obj.tipo, '#7f8c8d')
        return format_html('<span style="color: {};">{}</span>', 
                          color, obj.get_tipo_display())
    tipo_display.short_description = _("Tipo")
    
    def producto_display(self, obj):
        """Muestra el producto con formato."""
        return format_html('<span title="{}">{}</span>', 
                          obj.inventario.producto.nombre, obj.inventario.producto.codigo)
    producto_display.short_description = _("Producto")
    
    def almacen_display(self, obj):
        """Muestra el almacén con formato."""
        return obj.inventario.almacen.nombre
    almacen_display.short_description = _("Almacén")
    
    def cantidad_display(self, obj):
        """Muestra la cantidad con formato."""
        if obj.es_incremento:
            return format_html('<span style="color: #27ae60;">+{:.3f}</span>', obj.cantidad)
        else:
            return format_html('<span style="color: #e74c3c;">-{:.3f}</span>', obj.cantidad)
    cantidad_display.short_description = _("Cantidad")
