from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Q
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta
from shared_models.models import Producto
from almacenes.models import Almacen, Ubicacion


class TipoMovimiento(models.TextChoices):
    """Opciones para el tipo de movimiento de inventario"""
    ENTRADA = 'entrada', _('Entrada')
    SALIDA = 'salida', _('Salida')
    TRASLADO = 'traslado', _('Traslado')
    AJUSTE = 'ajuste', _('Ajuste')
    RESERVA = 'reserva', _('Reserva')
    LIBERACION = 'liberacion', _('Liberación')


class EstadoLote(models.TextChoices):
    """Opciones para el estado de un lote"""
    DISPONIBLE = 'disponible', _('Disponible')
    CUARENTENA = 'cuarentena', _('En cuarentena')
    BLOQUEADO = 'bloqueado', _('Bloqueado')
    VENCIDO = 'vencido', _('Vencido')
    AGOTADO = 'agotado', _('Agotado')


class Inventario(models.Model):
    """
    Modelo para gestionar el inventario de productos por ubicación.
    Permite llevar un control detallado del stock disponible y reservado.
    """
    inventario_id = models.AutoField(
        primary_key=True,
        verbose_name=_("ID del Inventario")
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='inventarios',
        verbose_name=_("Producto"),
        help_text=_("Producto al que pertenece este inventario")
    )
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.CASCADE,
        related_name='inventarios',
        verbose_name=_("Almacén"),
        help_text=_("Almacén donde se encuentra el inventario")
    )
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventarios',
        verbose_name=_("Ubicación"),
        help_text=_("Ubicación específica dentro del almacén")
    )
    lote = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Lote"),
        help_text=_("Número de lote para trazabilidad")
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Vencimiento"),
        help_text=_("Fecha de vencimiento del lote")
    )
    estado_lote = models.CharField(
        max_length=20,
        choices=EstadoLote.choices,
        default=EstadoLote.DISPONIBLE,
        verbose_name=_("Estado del Lote"),
        help_text=_("Estado actual del lote")
    )
    cantidad = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Cantidad"),
        help_text=_("Cantidad total disponible")
    )
    cantidad_reservada = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Cantidad Reservada"),
        help_text=_("Cantidad reservada para pedidos en proceso")
    )
    costo_unitario = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Costo Unitario"),
        help_text=_("Costo unitario de adquisición")
    )
    notas = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Notas"),
        help_text=_("Notas adicionales sobre este inventario")
    )
    # Metadatos flexibles
    metadatos = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Metadatos"),
        help_text=_("Metadatos flexibles sin necesidad de modificar el esquema")
    )
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Creación")
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de Actualización")
    )
    fecha_ultimo_movimiento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Último Movimiento"),
        help_text=_("Fecha del último movimiento de este inventario")
    )

    class Meta:
        verbose_name = _("Inventario")
        verbose_name_plural = _("Inventarios")
        ordering = ['almacen', 'producto', 'fecha_vencimiento']
        # Un producto puede estar en múltiples ubicaciones, pero solo una vez en cada ubicación con el mismo lote
        unique_together = [['producto', 'almacen', 'ubicacion', 'lote']]
        # Índices para mejorar el rendimiento de las consultas frecuentes
        indexes = [
            models.Index(fields=['producto', 'almacen']),
            models.Index(fields=['almacen', 'ubicacion']),
            models.Index(fields=['producto', 'estado_lote']),
            models.Index(fields=['fecha_vencimiento']),
        ]

    def __str__(self):
        ubicacion_str = f" en {self.ubicacion.codigo}" if self.ubicacion else ""
        lote_str = f" (Lote: {self.lote})" if self.lote else ""
        return f"{self.producto.nombre}{ubicacion_str}{lote_str}: {self.cantidad_disponible}"

    def clean(self):
        """
        Validaciones adicionales para el modelo.
        """
        super().clean()

        # Validar que la ubicación pertenezca al almacén
        if self.ubicacion and self.ubicacion.almacen != self.almacen:
            raise ValidationError({
                'ubicacion': _("La ubicación debe pertenecer al almacén seleccionado.")
            })

        # Validar que la cantidad reservada no sea mayor que la cantidad total
        if self.cantidad_reservada > self.cantidad:
            raise ValidationError({
                'cantidad_reservada': _("La cantidad reservada no puede ser mayor que la cantidad total.")
            })

        # Validar estado del lote según fecha de vencimiento
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date() and self.estado_lote != EstadoLote.VENCIDO:
            raise ValidationError({
                'estado_lote': _("El lote está vencido, debe tener estado 'Vencido'.")
            })

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para realizar validaciones antes de guardar.
        """
        self.clean()

        # Actualizar el stock del producto
        if not self.pk:  # Si es un nuevo registro
            Producto.objects.filter(pk=self.producto.pk).update(
                stock=F('stock') + self.cantidad
            )
        else:  # Si es una actualización
            old_instance = Inventario.objects.get(pk=self.pk)
            stock_diff = self.cantidad - old_instance.cantidad
            if stock_diff != 0:
                Producto.objects.filter(pk=self.producto.pk).update(
                    stock=F('stock') + stock_diff
                )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Sobrescribe el método delete para actualizar el stock del producto.
        """
        # Actualizar el stock del producto
        Producto.objects.filter(pk=self.producto.pk).update(
            stock=F('stock') - self.cantidad
        )

        super().delete(*args, **kwargs)

    @property
    def cantidad_disponible(self):
        """
        Calcula la cantidad realmente disponible (total - reservada).
        """
        return self.cantidad - self.cantidad_reservada

    @property
    def valor_total(self):
        """
        Calcula el valor total del inventario.
        """
        if self.costo_unitario is None:
            return None
        return self.cantidad * self.costo_unitario

    @property
    def esta_vencido(self):
        """
        Indica si el lote está vencido.
        """
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < timezone.now().date()

    @property
    def dias_para_vencer(self):
        """
        Calcula los días restantes hasta el vencimiento.
        """
        if not self.fecha_vencimiento:
            return None

        dias = (self.fecha_vencimiento - timezone.now().date()).days
        return max(0, dias)  # No mostrar días negativos

    def reservar(self, cantidad, referencia=None):
        """
        Reserva una cantidad del inventario.

        Args:
            cantidad: Cantidad a reservar
            referencia: Referencia opcional (ej: número de pedido)

        Returns:
            bool: True si la reserva fue exitosa, False en caso contrario

        Raises:
            ValidationError: Si la cantidad a reservar es mayor que la disponible
        """
        if cantidad <= 0:
            raise ValidationError(_("La cantidad a reservar debe ser mayor que cero."))

        if cantidad > self.cantidad_disponible:
            raise ValidationError(_("No hay suficiente stock disponible para reservar."))

        self.cantidad_reservada += cantidad
        self.fecha_ultimo_movimiento = timezone.now()

        # Registrar el movimiento
        MovimientoInventario.objects.create(
            inventario=self,
            tipo=TipoMovimiento.RESERVA,
            cantidad=cantidad,
            referencia=referencia,
            notas=f"Reserva de {cantidad} unidades"
        )

        self.save()
        return True

    def liberar(self, cantidad, referencia=None):
        """
        Libera una cantidad previamente reservada.

        Args:
            cantidad: Cantidad a liberar
            referencia: Referencia opcional (ej: número de pedido)

        Returns:
            bool: True si la liberación fue exitosa, False en caso contrario

        Raises:
            ValidationError: Si la cantidad a liberar es mayor que la reservada
        """
        if cantidad <= 0:
            raise ValidationError(_("La cantidad a liberar debe ser mayor que cero."))

        if cantidad > self.cantidad_reservada:
            raise ValidationError(_("La cantidad a liberar es mayor que la cantidad reservada."))

        self.cantidad_reservada -= cantidad
        self.fecha_ultimo_movimiento = timezone.now()

        # Registrar el movimiento
        MovimientoInventario.objects.create(
            inventario=self,
            tipo=TipoMovimiento.LIBERACION,
            cantidad=cantidad,
            referencia=referencia,
            notas=f"Liberación de {cantidad} unidades"
        )

        self.save()
        return True

    def ajustar(self, nueva_cantidad, motivo):
        """
        Ajusta la cantidad total del inventario.

        Args:
            nueva_cantidad: Nueva cantidad total
            motivo: Motivo del ajuste

        Returns:
            bool: True si el ajuste fue exitoso, False en caso contrario
        """
        if nueva_cantidad < 0:
            raise ValidationError(_("La cantidad no puede ser negativa."))

        if nueva_cantidad < self.cantidad_reservada:
            raise ValidationError(_("La nueva cantidad es menor que la cantidad reservada."))

        diferencia = nueva_cantidad - self.cantidad
        self.cantidad = nueva_cantidad
        self.fecha_ultimo_movimiento = timezone.now()

        # Registrar el movimiento
        MovimientoInventario.objects.create(
            inventario=self,
            tipo=TipoMovimiento.AJUSTE,
            cantidad=abs(diferencia),
            es_incremento=(diferencia > 0),
            notas=f"Ajuste de inventario: {motivo}"
        )

        self.save()
        return True

    @classmethod
    def get_stock_total_producto(cls, producto_id):
        """
        Obtiene el stock total disponible de un producto en todos los almacenes.

        Args:
            producto_id: ID del producto

        Returns:
            Decimal: Cantidad total disponible
        """
        resultado = cls.objects.filter(
            producto_id=producto_id,
            estado_lote=EstadoLote.DISPONIBLE
        ).aggregate(
            total=Sum(F('cantidad') - F('cantidad_reservada'))
        )

        return resultado['total'] or Decimal('0.00')

    @classmethod
    def get_stock_por_almacen(cls, producto_id):
        """
        Obtiene el stock disponible de un producto por almacén.

        Args:
            producto_id: ID del producto

        Returns:
            dict: Diccionario con el stock por almacén
        """
        resultados = cls.objects.filter(
            producto_id=producto_id,
            estado_lote=EstadoLote.DISPONIBLE
        ).values('almacen__nombre').annotate(
            disponible=Sum(F('cantidad') - F('cantidad_reservada'))
        ).order_by('almacen__nombre')

        return {r['almacen__nombre']: r['disponible'] for r in resultados}


class MovimientoInventario(models.Model):
    """
    Modelo para registrar los movimientos de inventario.
    Permite llevar un historial detallado de entradas, salidas, traslados, etc.
    """
    movimiento_id = models.AutoField(
        primary_key=True,
        verbose_name=_("ID del Movimiento")
    )
    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name='movimientos',
        verbose_name=_("Inventario"),
        help_text=_("Inventario al que pertenece este movimiento")
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoMovimiento.choices,
        verbose_name=_("Tipo de Movimiento"),
        help_text=_("Tipo de movimiento realizado")
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha"),
        help_text=_("Fecha y hora del movimiento")
    )
    cantidad = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        verbose_name=_("Cantidad"),
        help_text=_("Cantidad involucrada en el movimiento")
    )
    es_incremento = models.BooleanField(
        default=True,
        verbose_name=_("Es Incremento"),
        help_text=_("Indica si el movimiento incrementa o reduce el inventario")
    )
    ubicacion_origen = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_origen',
        verbose_name=_("Ubicación Origen"),
        help_text=_("Ubicación de origen para traslados")
    )
    ubicacion_destino = models.ForeignKey(
        Ubicacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_destino',
        verbose_name=_("Ubicación Destino"),
        help_text=_("Ubicación de destino para traslados")
    )
    referencia = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Referencia"),
        help_text=_("Referencia externa (ej: número de pedido, factura, etc.)")
    )
    codigo_seguimiento = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("Código de Seguimiento"),
        help_text=_("Código único para seguimiento del movimiento")
    )
    usuario = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Usuario"),
        help_text=_("Usuario que realizó el movimiento")
    )
    notas = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Notas"),
        help_text=_("Notas adicionales sobre este movimiento")
    )

    class Meta:
        verbose_name = _("Movimiento de Inventario")
        verbose_name_plural = _("Movimientos de Inventario")
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['tipo']),
            models.Index(fields=['referencia']),
            models.Index(fields=['codigo_seguimiento']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.inventario.producto.nombre} - {self.cantidad} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"


# Modelos para Class Table Inheritance de Producto

class TipoConservacion(models.TextChoices):
    """Opciones para el tipo de conservación de alimentos"""
    REFRIGERADO = 'refrigerado', _('Refrigerado')
    CONGELADO = 'congelado', _('Congelado')
    AMBIENTE = 'ambiente', _('Temperatura ambiente')
    FRESCO = 'fresco', _('Fresco')
    SECO = 'seco', _('Seco')


class CategoriaAlimento(models.TextChoices):
    """Opciones para la categoría de alimentos"""
    LACTEO = 'lacteo', _('Lácteo')
    CARNE = 'carne', _('Carne')
    PESCADO = 'pescado', _('Pescado')
    FRUTA = 'fruta', _('Fruta')
    VERDURA = 'verdura', _('Verdura')
    CEREAL = 'cereal', _('Cereal')
    LEGUMBRE = 'legumbre', _('Legumbre')
    BEBIDA = 'bebida', _('Bebida')
    SNACK = 'snack', _('Snack')
    CONGELADO = 'congelado', _('Congelado')
    ENLATADO = 'enlatado', _('Enlatado')
    PANADERIA = 'panaderia', _('Panadería')
    OTRO = 'otro', _('Otro')


class TipoElectronico(models.TextChoices):
    """Opciones para el tipo de producto electrónico"""
    COMPUTADORA = 'computadora', _('Computadora')
    TELEFONO = 'telefono', _('Teléfono')
    TABLET = 'tablet', _('Tablet')
    TELEVISION = 'television', _('Televisión')
    AUDIO = 'audio', _('Audio')
    CAMARA = 'camara', _('Cámara')
    VIDEOJUEGO = 'videojuego', _('Videojuego')
    ELECTRODOMESTICO = 'electrodomestico', _('Electrodoméstico')
    COMPONENTE = 'componente', _('Componente')
    ACCESORIO = 'accesorio', _('Accesorio')
    OTRO = 'otro', _('Otro')


class ProductoAlimento(Producto):
    """
    Modelo para productos de tipo alimento.
    Hereda de Producto e incluye campos específicos para alimentos.
    """
    fecha_elaboracion = models.DateField(
        verbose_name=_("Fecha de Elaboración"),
        help_text=_("Fecha en que fue elaborado el producto")
    )
    fecha_expiracion = models.DateField(
        verbose_name=_("Fecha de Expiración"),
        help_text=_("Fecha en que expira el producto")
    )
    ingredientes = models.TextField(
        verbose_name=_("Ingredientes"),
        help_text=_("Lista de ingredientes del producto")
    )
    permiso_sanitario = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Permiso Sanitario"),
        help_text=_("Número de permiso sanitario o registro sanitario")
    )
    # Campos adicionales recomendados
    tipo_conservacion = models.CharField(
        max_length=20,
        choices=TipoConservacion.choices,
        default=TipoConservacion.AMBIENTE,
        verbose_name=_("Tipo de Conservación"),
        help_text=_("Método de conservación recomendado")
    )
    temperatura_minima = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Temperatura Mínima (°C)"),
        help_text=_("Temperatura mínima de conservación en grados Celsius")
    )
    temperatura_maxima = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Temperatura Máxima (°C)"),
        help_text=_("Temperatura máxima de conservación en grados Celsius")
    )
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaAlimento.choices,
        default=CategoriaAlimento.OTRO,
        verbose_name=_("Categoría"),
        help_text=_("Categoría del alimento")
    )
    es_organico = models.BooleanField(
        default=False,
        verbose_name=_("Es Orgánico"),
        help_text=_("Indica si el producto es orgánico")
    )
    contiene_alergenos = models.BooleanField(
        default=False,
        verbose_name=_("Contiene Alérgenos"),
        help_text=_("Indica si el producto contiene alérgenos")
    )
    alergenos = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Alérgenos"),
        help_text=_("Lista de alérgenos presentes en el producto")
    )
    informacion_nutricional = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Información Nutricional"),
        help_text=_("Información nutricional en formato JSON")
    )
    pais_origen = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("País de Origen"),
        help_text=_("País de origen del producto")
    )

    class Meta:
        verbose_name = _("Producto Alimenticio")
        verbose_name_plural = _("Productos Alimenticios")

    def __str__(self):
        return f"{self.nombre} (Alimento)"

    def clean(self):
        """
        Validaciones adicionales para el modelo.
        """
        super().clean()

        # Validar que la fecha de expiración sea posterior a la fecha de elaboración
        if self.fecha_elaboracion and self.fecha_expiracion and self.fecha_elaboracion > self.fecha_expiracion:
            raise ValidationError({
                'fecha_expiracion': _("La fecha de expiración debe ser posterior a la fecha de elaboración.")
            })

        # Validar temperaturas si aplica
        if self.temperatura_minima is not None and self.temperatura_maxima is not None:
            if self.temperatura_minima > self.temperatura_maxima:
                raise ValidationError({
                    'temperatura_minima': _("La temperatura mínima no puede ser mayor que la temperatura máxima.")
                })

    @property
    def esta_vencido(self):
        """
        Indica si el producto está vencido.
        """
        return self.fecha_expiracion < timezone.now().date()

    @property
    def dias_para_vencer(self):
        """
        Calcula los días restantes hasta el vencimiento.
        """
        dias = (self.fecha_expiracion - timezone.now().date()).days
        return max(0, dias)  # No mostrar días negativos

    @property
    def vida_util_total(self):
        """
        Calcula la vida útil total del producto en días.
        """
        return (self.fecha_expiracion - self.fecha_elaboracion).days

    @property
    def porcentaje_vida_util_restante(self):
        """
        Calcula el porcentaje de vida útil restante.
        """
        if self.esta_vencido:
            return 0

        vida_util_total = self.vida_util_total
        if vida_util_total <= 0:
            return 0

        dias_transcurridos = (timezone.now().date() - self.fecha_elaboracion).days
        porcentaje_transcurrido = (dias_transcurridos / vida_util_total) * 100
        return max(0, 100 - porcentaje_transcurrido)


class ProductoElectronico(Producto):
    """
    Modelo para productos de tipo electrónico.
    Hereda de Producto e incluye campos específicos para electrónicos.
    """
    modelo = models.CharField(
        max_length=100,
        verbose_name=_("Modelo"),
        help_text=_("Modelo del producto electrónico")
    )
    version_firmware = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Versión de Firmware"),
        help_text=_("Versión actual del firmware")
    )
    version_software = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Versión de Software"),
        help_text=_("Versión actual del software")
    )
    voltaje = models.CharField(
        max_length=50,
        verbose_name=_("Voltaje"),
        help_text=_("Voltaje de operación (ej: 110V, 220V, 110-240V)")
    )
    garantia_meses = models.PositiveIntegerField(
        verbose_name=_("Garantía (meses)"),
        help_text=_("Duración de la garantía en meses")
    )
    # Campos adicionales recomendados
    tipo = models.CharField(
        max_length=20,
        choices=TipoElectronico.choices,
        default=TipoElectronico.OTRO,
        verbose_name=_("Tipo"),
        help_text=_("Tipo de producto electrónico")
    )
    numero_serie = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Número de Serie"),
        help_text=_("Número de serie del fabricante")
    )
    fabricante = models.CharField(
        max_length=100,
        verbose_name=_("Fabricante"),
        help_text=_("Nombre del fabricante")
    )
    pais_origen = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("País de Origen"),
        help_text=_("País de fabricación")
    )
    potencia = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Potencia"),
        help_text=_("Potencia en watts (ej: 100W)")
    )
    consumo_energia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Consumo de Energía (kWh)"),
        help_text=_("Consumo de energía en kilowatts-hora")
    )
    dimensiones = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Dimensiones"),
        help_text=_("Dimensiones del producto (ej: 10x20x30 cm)")
    )
    peso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Peso (kg)"),
        help_text=_("Peso en kilogramos")
    )
    conectividad = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Conectividad"),
        help_text=_("Opciones de conectividad en formato JSON (ej: WiFi, Bluetooth, USB)")
    )
    certificaciones = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Certificaciones"),
        help_text=_("Certificaciones del producto en formato JSON (ej: CE, FCC, RoHS)")
    )
    es_reconstruido = models.BooleanField(
        default=False,
        verbose_name=_("Es Reconstruido"),
        help_text=_("Indica si el producto es reconstruido (refurbished)")
    )

    class Meta:
        verbose_name = _("Producto Electrónico")
        verbose_name_plural = _("Productos Electrónicos")

    def __str__(self):
        return f"{self.nombre} (Electrónico)"

    @property
    def garantia_valida_hasta(self):
        """
        Calcula la fecha hasta la que es válida la garantía.
        """
        if not self.fecha_creacion:
            return None

        return self.fecha_creacion.date() + timedelta(days=self.garantia_meses * 30)

    @property
    def garantia_vigente(self):
        """
        Indica si la garantía está vigente.
        """
        if not self.fecha_creacion:
            return False

        return timezone.now().date() <= self.garantia_valida_hasta

    @property
    def dias_restantes_garantia(self):
        """
        Calcula los días restantes de garantía.
        """
        if not self.garantia_vigente:
            return 0

        dias = (self.garantia_valida_hasta - timezone.now().date()).days
        return max(0, dias)  # No mostrar días negativos

    def necesita_actualizacion_firmware(self, ultima_version):
        """
        Verifica si el producto necesita actualización de firmware.

        Args:
            ultima_version: Última versión disponible del firmware

        Returns:
            bool: True si necesita actualización, False en caso contrario
        """
        if not self.version_firmware:
            return False

        # Implementación simple, en la práctica se necesitaría una comparación más sofisticada
        return self.version_firmware != ultima_version
