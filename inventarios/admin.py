from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Sum, F
from .models import (
    Inventario, MovimientoInventario, EstadoLote,
    ProductoAlimento, ProductoElectronico,
    TipoConservacion, CategoriaAlimento, TipoElectronico
)


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


@admin.register(ProductoAlimento)
class ProductoAlimentoAdmin(admin.ModelAdmin):
    """
    Admin para el modelo ProductoAlimento.
    """
    list_display = ('producto_id', 'nombre', 'codigo', 'categoria_display',
                    'fecha_expiracion', 'dias_para_vencer_display',
                    'tipo_conservacion_display', 'es_organico_display')
    list_filter = ('categoria_alimento', 'tipo_conservacion', 'es_organico', 'contiene_alergenos')
    search_fields = ('nombre', 'codigo', 'marca', 'descripcion', 'ingredientes')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'dias_para_vencer',
                       'vida_util_total', 'porcentaje_vida_util_restante', 'esta_vencido')

    fieldsets = (
        (_('Información Básica'), {
            'fields': ('nombre', 'marca', 'descripcion', 'codigo', 'moneda', 'precio_venta', 'exento_iva', 'costo')
        }),
        (_('Información de Alimento'), {
            'fields': ('categoria_alimento', 'ingredientes', 'fecha_elaboracion', 'fecha_expiracion',
                      'dias_para_vencer', 'vida_util_total', 'porcentaje_vida_util_restante', 'esta_vencido')
        }),
        (_('Conservación'), {
            'fields': ('tipo_conservacion', 'temperatura_minima', 'temperatura_maxima')
        }),
        (_('Información Adicional'), {
            'fields': ('es_organico', 'contiene_alergenos', 'alergenos', 'permiso_sanitario',
                      'pais_origen', 'informacion_nutricional')
        }),
        (_('Inventario'), {
            'fields': ('unidad_medida', 'stock', 'alerta_stock')
        }),
        (_('Información del Sistema'), {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def categoria_display(self, obj):
        """Muestra la categoría con formato."""
        return obj.get_categoria_alimento_display()
    categoria_display.short_description = _("Categoría")

    def tipo_conservacion_display(self, obj):
        """Muestra el tipo de conservación con formato."""
        color_map = {
            'refrigerado': '#3498db',  # Azul
            'congelado': '#2980b9',    # Azul oscuro
            'ambiente': '#27ae60',     # Verde
            'fresco': '#2ecc71',       # Verde claro
            'seco': '#f39c12',         # Naranja
        }
        color = color_map.get(obj.tipo_conservacion, '#7f8c8d')
        return format_html('<span style="color: {};">{}</span>',
                          color, obj.get_tipo_conservacion_display())
    tipo_conservacion_display.short_description = _("Conservación")

    def es_organico_display(self, obj):
        """Muestra si es orgánico con formato."""
        if obj.es_organico:
            return format_html('<span style="color: #27ae60;">✓</span>')
        return format_html('<span style="color: #7f8c8d;">✗</span>')
    es_organico_display.short_description = _("Orgánico")

    def dias_para_vencer_display(self, obj):
        """Muestra los días para vencer con formato."""
        if obj.esta_vencido:
            return format_html('<span style="color: #e74c3c;">Vencido</span>')
        elif obj.dias_para_vencer <= 30:
            return format_html('<span style="color: #e67e22;">{} días</span>', obj.dias_para_vencer)
        else:
            return format_html('{} días', obj.dias_para_vencer)
    dias_para_vencer_display.short_description = _("Días para vencer")


@admin.register(ProductoElectronico)
class ProductoElectronicoAdmin(admin.ModelAdmin):
    """
    Admin para el modelo ProductoElectronico.
    """
    list_display = ('producto_id', 'nombre', 'codigo', 'tipo_display',
                    'fabricante', 'modelo', 'garantia_display',
                    'voltaje', 'es_reconstruido_display')
    list_filter = ('tipo', 'fabricante', 'es_reconstruido', 'garantia_meses')
    search_fields = ('nombre', 'codigo', 'marca', 'descripcion', 'modelo', 'numero_serie')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'garantia_valida_hasta',
                       'garantia_vigente', 'dias_restantes_garantia')

    fieldsets = (
        (_('Información Básica'), {
            'fields': ('nombre', 'marca', 'descripcion', 'codigo', 'moneda', 'precio_venta', 'exento_iva', 'costo')
        }),
        (_('Información de Electrónico'), {
            'fields': ('tipo', 'fabricante', 'modelo', 'numero_serie', 'pais_origen')
        }),
        (_('Especificaciones Técnicas'), {
            'fields': ('voltaje', 'potencia', 'consumo_energia', 'dimensiones', 'peso')
        }),
        (_('Software y Firmware'), {
            'fields': ('version_firmware', 'version_software')
        }),
        (_('Garantía'), {
            'fields': ('garantia_meses', 'garantia_valida_hasta', 'garantia_vigente', 'dias_restantes_garantia')
        }),
        (_('Información Adicional'), {
            'fields': ('es_reconstruido', 'conectividad', 'certificaciones')
        }),
        (_('Inventario'), {
            'fields': ('unidad_medida', 'stock', 'alerta_stock')
        }),
        (_('Información del Sistema'), {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def tipo_display(self, obj):
        """Muestra el tipo con formato."""
        return obj.get_tipo_display()
    tipo_display.short_description = _("Tipo")

    def garantia_display(self, obj):
        """Muestra la garantía con formato."""
        if not obj.garantia_vigente:
            return format_html('<span style="color: #e74c3c;">Vencida</span>')
        return format_html('<span style="color: #27ae60;">{} meses</span>', obj.garantia_meses)
    garantia_display.short_description = _("Garantía")

    def es_reconstruido_display(self, obj):
        """Muestra si es reconstruido con formato."""
        if obj.es_reconstruido:
            return format_html('<span style="color: #e67e22;">✓</span>')
        return format_html('<span style="color: #7f8c8d;">✗</span>')
    es_reconstruido_display.short_description = _("Reconstruido")
