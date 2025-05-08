from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


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

class Producto(models.Model):
    """
    Modelo para representar productos en el sistema ERP.
    """
    # Opciones para el campo unidad_medida
    UNIDAD_MEDIDA_CHOICES = [
        ('Kg', 'Kilogramos'),
        ('unidades', 'Unidades'),
        ('Cajas', 'Cajas'),
        ('Lts', 'Litros'),
    ]

    # La moneda ahora es una relación con el modelo Moneda

    # Campos del modelo
    producto_id = models.AutoField(primary_key=True, verbose_name="ID del Producto")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    marca = models.CharField(max_length=50, null=True, blank=True, verbose_name="Marca")
    descripcion = models.TextField(verbose_name="Descripción")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
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
        verbose_name="Precio de Venta"
    )
    exento_iva = models.BooleanField(
        default=False,
        verbose_name="Exento de IVA"
    )
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Costo"
    )
    unidad_medida = models.CharField(
        max_length=10,
        choices=UNIDAD_MEDIDA_CHOICES,
        verbose_name="Unidad de Medida"
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    alerta_stock = models.PositiveIntegerField(default=5, verbose_name="Alerta de Stock")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    @property
    def margen(self):
        """Calcula el margen de ganancia del producto."""
        if self.costo == 0:
            return 0
        return ((self.precio_venta - self.costo) / self.costo) * 100

    @property
    def stock_bajo(self):
        """Indica si el stock está por debajo del nivel de alerta."""
        return self.stock <= self.alerta_stock

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
