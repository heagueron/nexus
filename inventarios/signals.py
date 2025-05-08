from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, F
from django.utils import timezone
from .models import Inventario, MovimientoInventario, EstadoLote


@receiver(post_save, sender=Inventario)
def actualizar_capacidad_utilizada(sender, instance, **kwargs):
    """
    Actualiza la capacidad utilizada de la ubicación cuando se modifica el inventario.
    """
    if instance.ubicacion:
        # Calcular la capacidad utilizada total en la ubicación
        total_inventario = Inventario.objects.filter(
            ubicacion=instance.ubicacion
        ).aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        # Actualizar la capacidad utilizada de la ubicación
        # Nota: Esto es un placeholder, ya que el modelo Ubicacion no tiene un campo capacidad_utilizada
        # En el futuro, se podría añadir este campo al modelo Ubicacion
        pass


@receiver(post_save, sender=Inventario)
def verificar_vencimiento(sender, instance, **kwargs):
    """
    Verifica si el lote está vencido y actualiza su estado.
    """
    if instance.fecha_vencimiento and instance.fecha_vencimiento < timezone.now().date():
        if instance.estado_lote != EstadoLote.VENCIDO:
            # Actualizar el estado del lote a vencido
            instance.estado_lote = EstadoLote.VENCIDO
            instance.save(update_fields=['estado_lote'])
            
            # Registrar el cambio de estado
            MovimientoInventario.objects.create(
                inventario=instance,
                tipo='ajuste',
                cantidad=0,  # No hay cambio en la cantidad
                es_incremento=True,
                notas="Cambio automático de estado a VENCIDO"
            )
