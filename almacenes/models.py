from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from decimal import Decimal
import json
from shared_models.models import Producto


class TipoAlmacen(models.TextChoices):
    """Opciones para el tipo de almacén"""
    PRINCIPAL = 'principal', _('Principal')
    SECUNDARIO = 'secundario', _('Secundario')
    TRANSITO = 'transito', _('Tránsito')
    DEVOLUCION = 'devolucion', _('Devolución')
    OTRO = 'otro', _('Otro')


class UnidadMedidaCapacidad(models.TextChoices):
    """Opciones para la unidad de medida de capacidad"""
    METRO_CUBICO = 'm3', _('Metro cúbico')
    KILOGRAMO = 'kg', _('Kilogramo')
    PALLET = 'pallet', _('Pallet')
    UNIDAD = 'unidad', _('Unidad')
    OTRO = 'otro', _('Otro')


class TipoUbicacion(models.TextChoices):
    """Opciones para el tipo de ubicación dentro de un almacén"""
    ZONA = 'zona', _('Zona')
    PASILLO = 'pasillo', _('Pasillo')
    ESTANTERIA = 'estanteria', _('Estantería')
    NIVEL = 'nivel', _('Nivel')
    POSICION = 'posicion', _('Posición')
    OTRO = 'otro', _('Otro')


class Almacen(models.Model):
    """
    Modelo para representar almacenes físicos en el sistema ERP.
    Permite gestionar diferentes ubicaciones de inventario.
    """
    almacen_id = models.AutoField(
        primary_key=True,
        verbose_name=_("ID del Almacén")
    )
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nombre"),
        help_text=_("Nombre identificativo del almacén")
    )
    ubicacion = models.CharField(
        max_length=200,
        verbose_name=_("Ubicación"),
        help_text=_("Dirección física o ubicación del almacén")
    )
    descripcion = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_("Información adicional sobre el almacén"),
    )
    # Informacion de contacto y responsable
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Responsable"),
        help_text=_("Persona encargada del almacén"),
    )
    email_contacto = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
        verbose_name=_("Email de Contacto"),
        help_text=_("Email para comunicaciones relacionadas con el almacén"),
    )
    telefono_contacto = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Teléfono de Contacto"),
        help_text=_("Teléfono de contacto del almacén"),
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Creación")
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de Actualización")
    )
    horario_operacion = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Horario de Operación"),
        help_text=_("Horario de funcionamiento del almacén (ej. L-V 9am-5pm)"),
    )

    # Slug para URLs amigables
    slug = models.SlugField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("Identificador para URLs amigables"),
    )

    # Información geográfica y logística
    coordenadas_gps = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Coordenadas GPS"),
        help_text=_("Latitud y longitud para ubicación exacta (formato: 'lat,lng')"),
        validators=[
            RegexValidator(
                regex=r'^-?\d+(\.\d+)?,-?\d+(\.\d+)?$',
                message=_("Las coordenadas deben tener el formato 'latitud,longitud'")
            )
        ]
    )
    codigo_postal = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name=_("Código Postal"),
        help_text=_("Código postal para envíos y recepción de mercancía"),
    )
    ciudad = models.CharField(
        max_length=50,
        verbose_name=_("Ciudad"),
        help_text=_("Ciudad donde se encuentra el almacén"),
    )
    pais = models.CharField(
        max_length=50,
        default="Venezuela",
        verbose_name=_("País"),
        help_text=_("País donde se encuentra el almacén"),
    )

    # Capacidad y utilización
    area_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Área Total (m²)"),
        help_text=_("Área total del almacén en metros cuadrados"),
        validators=[MinValueValidator(0)]
    )
    tipo_almacen = models.CharField(
        max_length=20,
        choices=TipoAlmacen.choices,
        default=TipoAlmacen.PRINCIPAL,
        verbose_name=_("Tipo de Almacén"),
        help_text=_("Tipo o categoría del almacén"),
    )
    capacidad_maxima = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capacidad Máxima"),
        help_text=_("Capacidad máxima del almacén"),
        validators=[MinValueValidator(0)]
    )
    capacidad_utilizada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capacidad Utilizada"),
        help_text=_("Capacidad actualmente utilizada (calculada o manual)"),
        validators=[MinValueValidator(0)]
    )
    unidad_medida_capacidad = models.CharField(
        max_length=10,
        choices=UnidadMedidaCapacidad.choices,
        default=UnidadMedidaCapacidad.METRO_CUBICO,
        verbose_name=_("Unidad de Medida de Capacidad"),
        help_text=_("Unidad en que se mide la capacidad"),
    )

    # Estado y operatividad
    activo = models.BooleanField(
        default=True,
        verbose_name=_("Activo"),
        help_text=_("Indica si el almacén está activo o no"),
    )
    fecha_apertura = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Apertura"),
        help_text=_("Fecha en que comenzó a operar el almacén"),
    )
    fecha_cierre = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Fecha de Cierre"),
        help_text=_("Fecha de cierre (si aplica)"),
    )
    notas_operativas = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Notas Operativas"),
        help_text=_("Notas especiales sobre la operación del almacén"),
    )

    # Metadatos flexibles
    metadatos = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Metadatos"),
        help_text=_("Metadatos flexibles sin necesidad de modificar el esquema"),
    )

    class Meta:
        verbose_name = _("Almacén")
        verbose_name_plural = _("Almacenes")
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar automáticamente el slug
        y realizar otras validaciones antes de guardar.
        """
        # Generar slug si no existe
        if not self.slug:
            self.slug = slugify(self.nombre)

        # Validar fechas
        if self.fecha_cierre and self.fecha_apertura and self.fecha_cierre < self.fecha_apertura:
            raise ValidationError(_("La fecha de cierre no puede ser anterior a la fecha de apertura."))

        # Validar capacidad utilizada
        if self.capacidad_utilizada and self.capacidad_maxima and self.capacidad_utilizada > self.capacidad_maxima:
            raise ValidationError(_("La capacidad utilizada no puede ser mayor que la capacidad máxima."))

        super().save(*args, **kwargs)

    def clean(self):
        """
        Validaciones adicionales para el modelo.
        """
        super().clean()

        # Validar coordenadas GPS
        if self.coordenadas_gps:
            try:
                lat, lng = map(float, self.coordenadas_gps.split(','))
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    raise ValidationError({
                        'coordenadas_gps': _("Las coordenadas deben estar en rangos válidos: latitud [-90,90], longitud [-180,180].")
                    })
            except ValueError:
                raise ValidationError({
                    'coordenadas_gps': _("Las coordenadas deben ser números separados por coma.")
                })

    @property
    def porcentaje_ocupacion(self):
        """
        Calcula el porcentaje de ocupación del almacén.
        """
        if not self.capacidad_maxima or self.capacidad_maxima == 0:
            return 0

        if not self.capacidad_utilizada:
            return 0

        ocupacion = (self.capacidad_utilizada / self.capacidad_maxima) * 100
        return min(100, round(ocupacion, 2))  # Limitar a 100% máximo

    @property
    def estado(self):
        """
        Determina el estado del almacén basado en su ocupación.
        """
        ocupacion = self.porcentaje_ocupacion

        if ocupacion < 10:
            return _("Vacío")
        elif ocupacion < 50:
            return _("Disponible")
        elif ocupacion < 90:
            return _("Ocupado")
        else:
            return _("Lleno")

    def get_productos_disponibles(self):
        """
        Retorna la cantidad de productos diferentes disponibles en el almacén.
        """
        # Esta implementación es un placeholder hasta que tengamos el modelo de inventario
        # En el futuro, se implementará con una relación real
        return 0

    def get_valor_inventario(self):
        """
        Calcula el valor total del inventario en el almacén.
        """
        # Esta implementación es un placeholder hasta que tengamos el modelo de inventario
        # En el futuro, se implementará con una relación real
        return Decimal('0.00')

    def get_productos_bajo_stock(self):
        """
        Identifica productos con stock bajo en este almacén.
        """
        # Esta implementación es un placeholder hasta que tengamos el modelo de inventario
        # En el futuro, se implementará con una relación real
        return Producto.objects.none()

    def get_coordenadas_tuple(self):
        """
        Retorna las coordenadas como una tupla (latitud, longitud).
        """
        if not self.coordenadas_gps:
            return None

        try:
            lat, lng = map(float, self.coordenadas_gps.split(','))
            return (lat, lng)
        except (ValueError, TypeError):
            return None

    def set_metadato(self, clave, valor):
        """
        Establece un valor en el campo de metadatos.
        """
        if self.metadatos is None:
            self.metadatos = {}

        self.metadatos[clave] = valor
        self.save(update_fields=['metadatos'])

    def get_metadato(self, clave, default=None):
        """
        Obtiene un valor del campo de metadatos.
        """
        if not self.metadatos:
            return default

        return self.metadatos.get(clave, default)

    def generar_reporte_ocupacion(self):
        """
        Genera un reporte de ocupación del almacén.
        """
        return {
            'almacen': self.nombre,
            'tipo': self.get_tipo_almacen_display(),
            'capacidad_maxima': self.capacidad_maxima,
            'capacidad_utilizada': self.capacidad_utilizada,
            'unidad': self.get_unidad_medida_capacidad_display(),
            'porcentaje_ocupacion': self.porcentaje_ocupacion,
            'estado': self.estado,
            'fecha_reporte': self.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S')
        }


class Ubicacion(models.Model):
    """
    Modelo para representar ubicaciones específicas dentro de un almacén.
    Permite crear una estructura jerárquica de ubicaciones (zonas, pasillos, estanterías, niveles, posiciones).
    """
    ubicacion_id = models.AutoField(
        primary_key=True,
        verbose_name=_("ID de la Ubicación")
    )
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.CASCADE,
        related_name='ubicaciones',
        verbose_name=_("Almacén"),
        help_text=_("Almacén al que pertenece esta ubicación")
    )
    codigo = models.CharField(
        max_length=50,
        verbose_name=_("Código"),
        help_text=_("Código único de la ubicación dentro del almacén (ej: A-01-02-03)")
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre"),
        help_text=_("Nombre descriptivo de la ubicación (ej: Estantería A, Pasillo 1, Nivel 2, Posición 3)")
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoUbicacion.choices,
        default=TipoUbicacion.ZONA,
        verbose_name=_("Tipo de Ubicación"),
        help_text=_("Tipo o categoría de la ubicación")
    )
    padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='hijos',
        verbose_name=_("Ubicación Padre"),
        help_text=_("Ubicación que contiene a esta ubicación (para crear jerarquía)")
    )
    capacidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capacidad"),
        help_text=_("Capacidad máxima de la ubicación"),
        validators=[MinValueValidator(0)]
    )
    unidad_medida_capacidad = models.CharField(
        max_length=10,
        choices=UnidadMedidaCapacidad.choices,
        default=UnidadMedidaCapacidad.UNIDAD,
        verbose_name=_("Unidad de Medida de Capacidad"),
        help_text=_("Unidad en que se mide la capacidad")
    )
    activa = models.BooleanField(
        default=True,
        verbose_name=_("Activa"),
        help_text=_("Indica si la ubicación está activa o no")
    )
    descripcion = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Descripción"),
        help_text=_("Descripción adicional de la ubicación")
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

    class Meta:
        verbose_name = _("Ubicación")
        verbose_name_plural = _("Ubicaciones")
        ordering = ['almacen', 'codigo']
        unique_together = [['almacen', 'codigo']]

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.get_tipo_display()})"

    def clean(self):
        """
        Validaciones adicionales para el modelo.
        """
        super().clean()

        # Validar que el padre pertenezca al mismo almacén
        if self.padre and self.padre.almacen != self.almacen:
            raise ValidationError({
                'padre': _("La ubicación padre debe pertenecer al mismo almacén.")
            })

        # Validar que no haya ciclos en la jerarquía
        if self.padre:
            parent = self.padre
            while parent:
                if parent.pk == self.pk:
                    raise ValidationError({
                        'padre': _("Se ha detectado un ciclo en la jerarquía de ubicaciones.")
                    })
                parent = parent.padre

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para realizar validaciones antes de guardar.
        """
        self.clean()
        super().save(*args, **kwargs)

    @property
    def ruta_completa(self):
        """
        Retorna la ruta completa de la ubicación (incluyendo todos los padres).
        """
        if not self.padre:
            return self.nombre

        return f"{self.padre.ruta_completa} > {self.nombre}"

    @property
    def nivel_jerarquia(self):
        """
        Retorna el nivel de jerarquía de la ubicación (0 para ubicaciones sin padre).
        """
        if not self.padre:
            return 0

        return self.padre.nivel_jerarquia + 1

    def get_hijos_recursivos(self):
        """
        Retorna todos los hijos de la ubicación, recursivamente.
        """
        hijos = list(self.hijos.all())
        for hijo in list(hijos):  # Usar una copia para evitar problemas al modificar la lista
            hijos.extend(hijo.get_hijos_recursivos())
        return hijos

    def es_ancestro_de(self, ubicacion):
        """
        Verifica si esta ubicación es ancestro de la ubicación dada.
        """
        if not ubicacion.padre:
            return False

        if ubicacion.padre == self:
            return True

        return self.es_ancestro_de(ubicacion.padre)

    def es_descendiente_de(self, ubicacion):
        """
        Verifica si esta ubicación es descendiente de la ubicación dada.
        """
        return ubicacion.es_ancestro_de(self)

    def get_capacidad_disponible(self):
        """
        Calcula la capacidad disponible en la ubicación.
        """
        # Esta implementación es un placeholder hasta que tengamos el modelo de inventario
        # En el futuro, se implementará con una relación real
        return self.capacidad if self.capacidad else Decimal('0.00')

    def get_porcentaje_ocupacion(self):
        """
        Calcula el porcentaje de ocupación de la ubicación.
        """
        # Esta implementación es un placeholder hasta que tengamos el modelo de inventario
        # En el futuro, se implementará con una relación real
        return 0

    def set_metadato(self, clave, valor):
        """
        Establece un valor en el campo de metadatos.
        """
        if self.metadatos is None:
            self.metadatos = {}

        self.metadatos[clave] = valor
        self.save(update_fields=['metadatos'])

    def get_metadato(self, clave, default=None):
        """
        Obtiene un valor del campo de metadatos.
        """
        if not self.metadatos:
            return default

        return self.metadatos.get(clave, default)