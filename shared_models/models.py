from django.db import models
from django.core.validators import MinValueValidator, RegexValidator, EmailValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.cache import cache


def get_moneda_base_id():
    """
    Función para obtener el ID de la moneda base.
    Se usa como valor por defecto para el campo moneda en Producto.
    """
    from shared_models.models import Moneda
    try:
        moneda_base = Moneda.objects.get(es_base=True)
        return moneda_base.moneda_id
    except (Moneda.DoesNotExist, Moneda.MultipleObjectsReturned):
        return None

class EstadoProducto(models.TextChoices):
    """Opciones para el estado de un producto"""
    ACTIVO = 'activo', _('Activo')
    DESCONTINUADO = 'descontinuado', _('Descontinuado')
    AGOTADO = 'agotado', _('Agotado')
    SUSPENDIDO = 'suspendido', _('Suspendido')
    BORRADOR = 'borrador', _('Borrador')


class TipoImpuesto(models.TextChoices):
    """Opciones para el tipo de impuesto aplicable"""
    EXENTO = 'exento', _('Exento')
    GENERAL = 'general', _('General')
    REDUCIDO = 'reducido', _('Reducido')
    ADICIONAL = 'adicional', _('Adicional')


class Producto(models.Model):
    """
    Modelo base para representar productos en el sistema ERP.
    Sirve como clase base para la herencia de tipos específicos de productos.
    """
    # Opciones para el campo unidad_medida
    UNIDAD_MEDIDA_CHOICES = [
        ('kg', 'Kilogramos'),
        ('g', 'Gramos'),
        ('l', 'Litros'),
        ('ml', 'Mililitros'),
        ('unidad', 'Unidades'),
        ('caja', 'Cajas'),
        ('paquete', 'Paquetes'),
        ('docena', 'Docenas'),
        ('m', 'Metros'),
        ('cm', 'Centímetros'),
        ('m2', 'Metros cuadrados'),
        ('m3', 'Metros cúbicos'),
        ('par', 'Pares'),
        ('rollo', 'Rollos'),
        ('hora', 'Horas'),
        ('servicio', 'Servicio'),
        ('otro', 'Otro'),
    ]

    # Campos del modelo
    producto_id = models.AutoField(
        primary_key=True,
        verbose_name=_("ID del Producto")
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre"),
        help_text=_("Nombre comercial del producto")
    )
    marca = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Marca"),
        help_text=_("Marca del producto")
    )
    descripcion = models.TextField(
        verbose_name=_("Descripción"),
        help_text=_("Descripción detallada del producto")
    )
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Código"),
        help_text=_("Código único del producto")
    )
    codigo_barras = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Código de Barras"),
        help_text=_("Código de barras del producto (EAN, UPC, etc.)")
    )
    sku = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("SKU"),
        help_text=_("Stock Keeping Unit - Código interno de gestión")
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoProducto.choices,
        default=EstadoProducto.ACTIVO,
        verbose_name=_("Estado"),
        help_text=_("Estado actual del producto")
    )

    # Campos financieros
    moneda = models.ForeignKey(
        'Moneda',
        on_delete=models.PROTECT,  # Evita eliminar monedas que están en uso
        related_name='productos',
        verbose_name=_("Moneda"),
        help_text=_("Moneda en la que se expresan los precios del producto"),
        default=get_moneda_base_id
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Precio de Venta"),
        help_text=_("Precio de venta al público")
    )
    precio_mayorista = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_("Precio Mayorista"),
        help_text=_("Precio para ventas al por mayor")
    )
    precio_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_("Precio Mínimo"),
        help_text=_("Precio mínimo permitido para ventas")
    )
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Costo"),
        help_text=_("Costo de adquisición o producción")
    )
    tipo_impuesto = models.CharField(
        max_length=20,
        choices=TipoImpuesto.choices,
        default=TipoImpuesto.GENERAL,
        verbose_name=_("Tipo de Impuesto"),
        help_text=_("Tipo de impuesto aplicable al producto")
    )
    exento_iva = models.BooleanField(
        default=False,
        verbose_name=_("Exento de IVA"),
        help_text=_("Indica si el producto está exento de IVA")
    )

    # Campos de inventario
    unidad_medida = models.CharField(
        max_length=10,
        choices=UNIDAD_MEDIDA_CHOICES,
        verbose_name=_("Unidad de Medida"),
        help_text=_("Unidad de medida para el producto")
    )
    stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Stock"),
        help_text=_("Cantidad disponible en inventario")
    )
    alerta_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name=_("Alerta de Stock"),
        help_text=_("Cantidad mínima antes de generar alerta")
    )
    stock_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Stock Máximo"),
        help_text=_("Cantidad máxima recomendada en inventario")
    )
    es_inventariable = models.BooleanField(
        default=True,
        verbose_name=_("Es Inventariable"),
        help_text=_("Indica si el producto se gestiona en inventario")
    )

    # Campos de categorización
    categoria = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Categoría"),
        help_text=_("Categoría general del producto")
    )
    subcategoria = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Subcategoría"),
        help_text=_("Subcategoría del producto")
    )
    tags = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Etiquetas"),
        help_text=_("Etiquetas separadas por comas para facilitar búsquedas")
    )

    # Campos de metadatos
    metadatos = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Metadatos"),
        help_text=_("Información adicional en formato JSON")
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
    creado_por = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Creado Por"),
        help_text=_("Usuario que creó el registro")
    )
    actualizado_por = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Actualizado Por"),
        help_text=_("Usuario que actualizó por última vez el registro")
    )

    class Meta:
        verbose_name = _("Producto")
        verbose_name_plural = _("Productos")
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['codigo']),
            models.Index(fields=['estado']),
            models.Index(fields=['categoria']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def clean(self):
        """
        Validaciones adicionales para el modelo.
        """
        super().clean()

        # Validar que el precio mínimo no sea mayor que el precio de venta
        if self.precio_minimo is not None and self.precio_minimo > self.precio_venta:
            raise ValidationError({
                'precio_minimo': _("El precio mínimo no puede ser mayor que el precio de venta.")
            })

        # Validar que el precio mayorista no sea mayor que el precio de venta
        if self.precio_mayorista is not None and self.precio_mayorista > self.precio_venta:
            raise ValidationError({
                'precio_mayorista': _("El precio mayorista no puede ser mayor que el precio de venta.")
            })

        # Validar coherencia entre exento_iva y tipo_impuesto
        if self.exento_iva and self.tipo_impuesto != TipoImpuesto.EXENTO:
            self.tipo_impuesto = TipoImpuesto.EXENTO

        if not self.exento_iva and self.tipo_impuesto == TipoImpuesto.EXENTO:
            self.exento_iva = True

        # Validar stock máximo
        if self.stock_maximo is not None and self.stock_maximo < self.alerta_stock:
            raise ValidationError({
                'stock_maximo': _("El stock máximo no puede ser menor que la alerta de stock.")
            })

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para llamar a clean() antes de guardar.
        """
        self.clean()
        super().save(*args, **kwargs)

    # Propiedades financieras
    @property
    def margen(self):
        """
        Calcula el margen de ganancia del producto en porcentaje.

        Returns:
            float: Margen de ganancia en porcentaje
        """
        if self.costo == 0:
            return 0
        return ((self.precio_venta - self.costo) / self.costo) * 100

    @property
    def margen_valor(self):
        """
        Calcula el margen de ganancia del producto en valor absoluto.

        Returns:
            Decimal: Margen de ganancia en valor absoluto
        """
        return self.precio_venta - self.costo

    @property
    def rentabilidad(self):
        """
        Calcula la rentabilidad del producto (margen sobre precio de venta).

        Returns:
            float: Rentabilidad en porcentaje
        """
        if self.precio_venta == 0:
            return 0
        return ((self.precio_venta - self.costo) / self.precio_venta) * 100

    @property
    def precio_con_iva(self):
        """
        Calcula el precio con IVA incluido.

        Returns:
            Decimal: Precio con IVA
        """
        from django.conf import settings

        if self.exento_iva:
            return self.precio_venta

        # Obtener el porcentaje de IVA de la configuración
        try:
            empresa = Empresa.get_current()
            porcentaje_iva = empresa.porcentaje_iva
        except:
            # Valor por defecto si no se puede obtener
            porcentaje_iva = 16.0

        return self.precio_venta * (1 + (porcentaje_iva / 100))

    # Propiedades de inventario
    @property
    def stock_bajo(self):
        """
        Indica si el stock está por debajo del nivel de alerta.

        Returns:
            bool: True si el stock está por debajo del nivel de alerta
        """
        return self.stock <= self.alerta_stock

    @property
    def stock_alto(self):
        """
        Indica si el stock está por encima del nivel máximo.

        Returns:
            bool: True si el stock está por encima del nivel máximo
        """
        if self.stock_maximo is None:
            return False
        return self.stock >= self.stock_maximo

    @property
    def porcentaje_stock(self):
        """
        Calcula el porcentaje de stock respecto al máximo.

        Returns:
            float: Porcentaje de stock (0-100)
        """
        if self.stock_maximo is None or self.stock_maximo == 0:
            return 100 if self.stock > 0 else 0

        porcentaje = (self.stock / self.stock_maximo) * 100
        return min(100, porcentaje)  # No superar el 100%

    @property
    def valor_inventario(self):
        """
        Calcula el valor total del inventario para este producto.

        Returns:
            Decimal: Valor del inventario
        """
        return self.stock * self.costo

    # Métodos para conversión de moneda
    def _convertir_valor(self, valor, moneda_destino, usar_tasa_mercado=False):
        """
        Método interno para convertir un valor monetario a otra moneda.

        Args:
            valor: Valor a convertir
            moneda_destino: Instancia del modelo Moneda o ID de la moneda destino
            usar_tasa_mercado: Si es True, usa la tasa de mercado; si es False, usa la tasa oficial

        Returns:
            Decimal: Valor convertido a la moneda destino

        Raises:
            ValueError: Si la moneda destino no existe
            TypeError: Si el argumento no es una instancia de Moneda o un ID válido
        """
        # Si recibimos un ID, obtenemos la instancia de Moneda
        if isinstance(moneda_destino, int):
            try:
                moneda_destino = Moneda.objects.get(moneda_id=moneda_destino)
            except Moneda.DoesNotExist:
                raise ValueError(f"No existe una moneda con ID {moneda_destino}")

        # Verificamos que sea una instancia de Moneda
        if not isinstance(moneda_destino, Moneda):
            raise TypeError("El argumento debe ser una instancia de Moneda o un ID válido")

        # Si es la misma moneda, retornamos el valor sin cambios
        if self.moneda == moneda_destino:
            return valor

        # Determinamos qué tasa usar
        tasa_origen = self.moneda.tasa_mercado if usar_tasa_mercado else self.moneda.tasa_oficial
        tasa_destino = moneda_destino.tasa_mercado if usar_tasa_mercado else moneda_destino.tasa_oficial

        # Si la moneda del producto es la base
        if self.moneda.es_base:
            # Multiplicamos por la tasa de la moneda destino
            return valor * tasa_destino

        # Si la moneda destino es la base
        elif moneda_destino.es_base:
            # Dividimos por la tasa de la moneda del producto
            return valor / tasa_origen

        # Si ninguna es la base, convertimos a través de la moneda base
        else:
            # Primero convertimos a la moneda base
            valor_base = valor / tasa_origen
            # Luego convertimos de la moneda base a la destino
            return valor_base * tasa_destino

    def precio_en_moneda(self, moneda_destino, usar_tasa_mercado=False):
        """
        Calcula el precio del producto en otra moneda.

        Args:
            moneda_destino: Instancia del modelo Moneda o ID de la moneda destino
            usar_tasa_mercado: Si es True, usa la tasa de mercado; si es False, usa la tasa oficial (por defecto)

        Returns:
            Decimal: Precio convertido a la moneda destino

        Raises:
            ValueError: Si la moneda destino no existe
            TypeError: Si el argumento no es una instancia de Moneda o un ID válido
        """
        return self._convertir_valor(self.precio_venta, moneda_destino, usar_tasa_mercado)

    def precio_mayorista_en_moneda(self, moneda_destino, usar_tasa_mercado=False):
        """
        Calcula el precio mayorista del producto en otra moneda.

        Args:
            moneda_destino: Instancia del modelo Moneda o ID de la moneda destino
            usar_tasa_mercado: Si es True, usa la tasa de mercado; si es False, usa la tasa oficial (por defecto)

        Returns:
            Decimal: Precio mayorista convertido a la moneda destino

        Raises:
            ValueError: Si la moneda destino no existe o si el producto no tiene precio mayorista
            TypeError: Si el argumento no es una instancia de Moneda o un ID válido
        """
        if self.precio_mayorista is None:
            return None
        return self._convertir_valor(self.precio_mayorista, moneda_destino, usar_tasa_mercado)

    def costo_en_moneda(self, moneda_destino, usar_tasa_mercado=False):
        """
        Calcula el costo del producto en otra moneda.

        Args:
            moneda_destino: Instancia del modelo Moneda o ID de la moneda destino
            usar_tasa_mercado: Si es True, usa la tasa de mercado; si es False, usa la tasa oficial (por defecto)

        Returns:
            Decimal: Costo convertido a la moneda destino

        Raises:
            ValueError: Si la moneda destino no existe
            TypeError: Si el argumento no es una instancia de Moneda o un ID válido
        """
        return self._convertir_valor(self.costo, moneda_destino, usar_tasa_mercado)

    def precio_formateado(self, moneda=None, usar_tasa_mercado=False):
        """
        Devuelve el precio del producto formateado con el símbolo de la moneda.

        Args:
            moneda: Instancia del modelo Moneda, ID de la moneda o None para usar la moneda del producto
            usar_tasa_mercado: Si es True, usa la tasa de mercado; si es False, usa la tasa oficial (por defecto)

        Returns:
            str: Precio formateado con el símbolo de la moneda

        Raises:
            ValueError: Si la moneda no existe
            TypeError: Si el argumento no es una instancia de Moneda, un ID válido o None
        """
        if moneda is None:
            # Usar la moneda del producto
            precio = self.precio_venta
            simbolo = self.moneda.simbolo
        else:
            # Convertir a la moneda especificada
            precio = self.precio_en_moneda(moneda, usar_tasa_mercado)

            # Obtener el símbolo de la moneda
            if isinstance(moneda, int):
                try:
                    simbolo = Moneda.objects.get(moneda_id=moneda).simbolo
                except Moneda.DoesNotExist:
                    raise ValueError(f"No existe una moneda con ID {moneda}")
            elif isinstance(moneda, Moneda):
                simbolo = moneda.simbolo
            else:
                raise TypeError("El argumento debe ser una instancia de Moneda, un ID válido o None")

        # Formatear el precio con el símbolo
        return f"{simbolo} {precio:,.2f}"

    def costo_formateado(self, moneda=None, usar_tasa_mercado=False):
        """
        Devuelve el costo del producto formateado con el símbolo de la moneda.

        Args:
            moneda: Instancia del modelo Moneda, ID de la moneda o None para usar la moneda del producto
            usar_tasa_mercado: Si es True, usa la tasa de mercado; si es False, usa la tasa oficial (por defecto)

        Returns:
            str: Costo formateado con el símbolo de la moneda

        Raises:
            ValueError: Si la moneda no existe
            TypeError: Si el argumento no es una instancia de Moneda, un ID válido o None
        """
        if moneda is None:
            # Usar la moneda del producto
            costo = self.costo
            simbolo = self.moneda.simbolo
        else:
            # Convertir a la moneda especificada
            costo = self.costo_en_moneda(moneda, usar_tasa_mercado)

            # Obtener el símbolo de la moneda
            if isinstance(moneda, int):
                try:
                    simbolo = Moneda.objects.get(moneda_id=moneda).simbolo
                except Moneda.DoesNotExist:
                    raise ValueError(f"No existe una moneda con ID {moneda}")
            elif isinstance(moneda, Moneda):
                simbolo = moneda.simbolo
            else:
                raise TypeError("El argumento debe ser una instancia de Moneda, un ID válido o None")

        # Formatear el costo con el símbolo
        return f"{simbolo} {costo:,.2f}"

    # Métodos de utilidad
    def get_tipo_producto(self):
        """
        Determina el tipo específico de producto.

        Returns:
            str: Tipo de producto ('base', 'alimento', 'electronico', etc.)
        """
        from inventarios.models import ProductoAlimento, ProductoElectronico

        try:
            if hasattr(self, 'productoalimento'):
                return 'alimento'
        except ProductoAlimento.DoesNotExist:
            pass

        try:
            if hasattr(self, 'productoelectronico'):
                return 'electronico'
        except ProductoElectronico.DoesNotExist:
            pass

        return 'base'

    def get_instancia_especifica(self):
        """
        Obtiene la instancia específica del producto (alimento, electrónico, etc.)

        Returns:
            Producto: Instancia específica del producto o self si es base
        """
        tipo = self.get_tipo_producto()

        if tipo == 'alimento':
            return self.productoalimento
        elif tipo == 'electronico':
            return self.productoelectronico

        return self

    @classmethod
    def buscar(cls, texto, incluir_inactivos=False):
        """
        Busca productos por texto en varios campos.

        Args:
            texto: Texto a buscar
            incluir_inactivos: Si es True, incluye productos no activos

        Returns:
            QuerySet: Productos que coinciden con la búsqueda
        """
        from django.db.models import Q

        query = Q(nombre__icontains=texto) | \
                Q(codigo__icontains=texto) | \
                Q(marca__icontains=texto) | \
                Q(descripcion__icontains=texto) | \
                Q(codigo_barras__icontains=texto) | \
                Q(sku__icontains=texto) | \
                Q(tags__icontains=texto)

        queryset = cls.objects.filter(query)

        if not incluir_inactivos:
            queryset = queryset.filter(estado=EstadoProducto.ACTIVO)

        return queryset


class Cliente(models.Model):
    """
    Modelo para representar clientes en el sistema ERP.
    """
    # Opciones para el campo tipo
    TIPO_CHOICES = [
        ('juridico', 'Jurídico'),
        ('natural', 'Natural'),
    ]

    # Validador para RIF
    rif_validator = RegexValidator(
        regex=r'^[VEJG][0-9]{9}$',
        message='El RIF debe tener el formato: V/E/J/G seguido de 9 dígitos.'
    )

    # Campos del modelo
    cliente_id = models.AutoField(primary_key=True, verbose_name="ID del Cliente")
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Cliente"
    )
    rif = models.CharField(
        max_length=10,
        validators=[rif_validator],
        unique=True,
        verbose_name="RIF"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    pais = models.CharField(max_length=50, default="Venezuela", verbose_name="País")
    direccion = models.TextField(verbose_name="Dirección")
    telefono = models.CharField(max_length=20, null=True, blank=True, verbose_name="Teléfono")
    nombre_contacto = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nombre de Contacto")
    telefono_contacto = models.CharField(max_length=20, null=True, blank=True, verbose_name="Teléfono de Contacto")
    comentario = models.TextField(null=True, blank=True, verbose_name="Comentario")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rif})"


class Moneda(models.Model):
    """
    Modelo para representar monedas y sus tasas de cambio en el sistema ERP.
    """

    @classmethod
    def get_moneda_base(cls):
        """
        Retorna la moneda base del sistema.
        Si no existe una moneda base, retorna None.
        """
        try:
            return cls.objects.get(es_base=True)
        except (cls.DoesNotExist, cls.MultipleObjectsReturned):
            return None
    moneda_id = models.AutoField(primary_key=True, verbose_name=_("ID de la Moneda"))
    nombre = models.CharField(max_length=30, unique=True, verbose_name=_("Nombre"))
    simbolo = models.CharField(max_length=10, verbose_name=_("Símbolo"))
    es_base = models.BooleanField(
        default=False,
        verbose_name=_("Es moneda base"),
        help_text=_("Indica si esta es la moneda base del sistema. Solo una moneda puede ser la base.")
    )
    tasa_oficial = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(0)],
        verbose_name=_("Tasa Oficial"),
        help_text=_("Tasa de cambio oficial con respecto a la moneda base")
    )
    tasa_mercado = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(0)],
        verbose_name=_("Tasa de Mercado"),
        help_text=_("Tasa de cambio del mercado con respecto a la moneda base")
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de Actualización"))

    class Meta:
        verbose_name = _("Moneda")
        verbose_name_plural = _("Monedas")
        ordering = ['nombre']

    def clean(self):
        """
        Valida que solo una moneda pueda ser marcada como base.
        Si esta moneda está marcada como base, verifica que no haya otra moneda base.
        """
        if self.es_base and Moneda.objects.exclude(pk=self.pk).filter(es_base=True).exists():
            raise ValidationError(_("Ya existe otra moneda marcada como base. Solo puede haber una moneda base en el sistema."))

        # Si es la moneda base, las tasas deben ser 1.0
        if self.es_base and (self.tasa_oficial != 1.0 or self.tasa_mercado != 1.0):
            self.tasa_oficial = 1.0
            self.tasa_mercado = 1.0

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para llamar a clean() antes de guardar.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        base_indicator = " (Base)" if self.es_base else ""
        return f"{self.nombre} ({self.simbolo}){base_indicator}"


class EmpresaManager(models.Manager):
    """
    Manager personalizado para el modelo Empresa que implementa el patrón singleton.
    """
    def get_current(self):
        """
        Retorna la única instancia de Empresa, o la crea si no existe.
        Utiliza caché para mejorar el rendimiento.
        """
        # Intentar obtener de caché primero
        empresa = cache.get('empresa_singleton')
        if empresa is not None:
            return empresa

        # Si no está en caché, intentar obtener de la base de datos
        try:
            empresa = self.get_queryset().get()
            # Guardar en caché
            cache.set('empresa_singleton', empresa, 3600)  # Caché por 1 hora
            return empresa
        except self.model.DoesNotExist:
            # Si no existe, crear una instancia con valores por defecto
            empresa = self.create(
                nombre_legal="Mi Empresa",
                nombre_comercial="Mi Empresa",
                rif="J000000000",
                porcentaje_iva=16.0
            )
            # Guardar en caché
            cache.set('empresa_singleton', empresa, 3600)
            return empresa
        except self.model.MultipleObjectsReturned:
            # Si hay múltiples instancias (no debería ocurrir), retornar la primera
            empresa = self.get_queryset().first()
            # Guardar en caché
            cache.set('empresa_singleton', empresa, 3600)
            return empresa


class Empresa(models.Model):
    """
    Modelo para representar la información y configuración de la empresa.
    Implementa el patrón singleton para asegurar que solo exista una instancia.
    """
    # Manager personalizado
    objects = EmpresaManager()

    # Información básica
    empresa_id = models.AutoField(primary_key=True, verbose_name=_("ID de la Empresa"))
    nombre_legal = models.CharField(
        max_length=100,
        verbose_name=_("Nombre Legal"),
        help_text=_("Nombre legal completo de la empresa")
    )
    nombre_comercial = models.CharField(
        max_length=100,
        verbose_name=_("Nombre Comercial"),
        help_text=_("Nombre comercial o marca de la empresa")
    )
    rif = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^[JVG]-[0-9]{8}$',
                message=_('El RIF debe tener el formato: J/V/G seguido de - seguido de 8 dígitos.')
            )
        ],
        verbose_name=_("RIF"),
        help_text=_("Registro de Información Fiscal")
    )
    logo = models.ImageField(
        upload_to='empresa/logos/',
        null=True,
        blank=True,
        verbose_name=_("Logo"),
        help_text=_("Logotipo de la empresa")
    )
    es_activa = models.BooleanField(
        default=True,
        verbose_name=_("Activa"),
        help_text=_("Indica si la empresa está activa")
    )

    # Contacto y ubicación
    direccion_fiscal = models.TextField(
        verbose_name=_("Dirección Fiscal"),
        help_text=_("Dirección fiscal completa")
    )
    ciudad = models.CharField(
        max_length=50,
        verbose_name=_("Ciudad"),
        help_text=_("Ciudad de la sede principal")
    )
    estado = models.CharField(
        max_length=50,
        verbose_name=_("Estado/Provincia"),
        help_text=_("Estado o provincia")
    )
    pais = models.CharField(
        max_length=50,
        default="Venezuela",
        verbose_name=_("País"),
        help_text=_("País de registro")
    )
    codigo_postal = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name=_("Código Postal"),
        help_text=_("Código postal")
    )
    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Teléfono"),
        help_text=_("Teléfono principal")
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Email"),
        help_text=_("Email corporativo")
    )
    sitio_web = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Sitio Web"),
        help_text=_("Sitio web de la empresa")
    )

    # Configuración fiscal
    moneda_base = models.ForeignKey(
        'Moneda',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='empresa_moneda_base',
        verbose_name=_("Moneda Base"),
        help_text=_("Moneda base para la empresa")
    )
    porcentaje_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=16.0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Porcentaje de IVA"),
        help_text=_("Porcentaje de IVA estándar")
    )
    aplica_retenciones = models.BooleanField(
        default=True,
        verbose_name=_("Aplica Retenciones"),
        help_text=_("Indica si la empresa aplica retenciones")
    )

    # Configuración del sistema
    formato_factura = models.CharField(
        max_length=50,
        default="FAC-{year}{month}-{sequence:04d}",
        verbose_name=_("Formato de Factura"),
        help_text=_("Formato para numeración de facturas")
    )
    formato_orden_compra = models.CharField(
        max_length=50,
        default="OC-{year}{month}-{sequence:04d}",
        verbose_name=_("Formato de Orden de Compra"),
        help_text=_("Formato para numeración de órdenes de compra")
    )
    dias_alerta_vencimiento = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Días Alerta Vencimiento"),
        help_text=_("Días para alertar sobre vencimientos")
    )

    # Metadatos flexibles
    configuracion_adicional = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Configuración Adicional"),
        help_text=_("Configuraciones adicionales en formato JSON")
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

    class Meta:
        verbose_name = _("Empresa")
        verbose_name_plural = _("Empresas")

    def clean(self):
        """
        Valida que solo exista una instancia de Empresa.
        """
        if not self.pk and Empresa.objects.exists():
            raise ValidationError(_("Ya existe una instancia de Empresa. Solo puede haber una."))

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para llamar a clean() antes de guardar
        y actualizar la caché después de guardar.
        """
        self.clean()
        super().save(*args, **kwargs)
        # Actualizar caché
        cache.set('empresa_singleton', self, 3600)

    def delete(self, *args, **kwargs):
        """
        Previene la eliminación de la única instancia.
        """
        if Empresa.objects.count() <= 1:
            raise ValidationError(_("No se puede eliminar la única instancia de Empresa."))
        # Limpiar caché
        cache.delete('empresa_singleton')
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.nombre_comercial

    @classmethod
    def get_current(cls):
        """
        Método de clase para obtener la instancia actual.
        Es un atajo para Empresa.objects.get_current().
        """
        return cls.objects.get_current()
