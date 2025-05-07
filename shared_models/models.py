from django.db import models
from django.core.validators import MinValueValidator

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

    # Opciones para el campo moneda
    MONEDA_CHOICES = [
        ('Bolivares', 'Bolívares'),
        ('USD', 'Dólares Estadounidenses'),
    ]

    # Campos del modelo
    producto_id = models.AutoField(primary_key=True, verbose_name="ID del Producto")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    marca = models.CharField(max_length=50, null=True, blank=True, verbose_name="Marca")
    descripcion = models.TextField(verbose_name="Descripción")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    moneda = models.CharField(
        max_length=10,
        choices=MONEDA_CHOICES,
        default='Bolivares',
        verbose_name="Moneda"
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
