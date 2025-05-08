from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import random
from datetime import timedelta
from decimal import Decimal
from shared_models.models import Producto
from almacenes.models import Almacen, Ubicacion
from inventarios.models import Inventario, MovimientoInventario, EstadoLote


class Command(BaseCommand):
    help = 'Genera inventarios de ejemplo para los productos y ubicaciones existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Elimina todos los inventarios existentes antes de crear los nuevos',
        )
        parser.add_argument(
            '--producto',
            type=int,
            help='ID del producto específico para el que generar inventarios',
        )
        parser.add_argument(
            '--almacen',
            type=int,
            help='ID del almacén específico para el que generar inventarios',
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=100,
            help='Cantidad total aproximada de inventarios a generar',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            # Obtener productos
            if options['producto']:
                productos = Producto.objects.filter(producto_id=options['producto'])
                if not productos.exists():
                    self.stdout.write(self.style.ERROR(f'No se encontró el producto con ID {options["producto"]}'))
                    return
            else:
                productos = Producto.objects.all()

            if not productos.exists():
                self.stdout.write(self.style.ERROR('No hay productos disponibles para generar inventarios'))
                return

            # Obtener almacenes
            if options['almacen']:
                almacenes = Almacen.objects.filter(almacen_id=options['almacen'])
                if not almacenes.exists():
                    self.stdout.write(self.style.ERROR(f'No se encontró el almacén con ID {options["almacen"]}'))
                    return
            else:
                almacenes = Almacen.objects.all()

            if not almacenes.exists():
                self.stdout.write(self.style.ERROR('No hay almacenes disponibles para generar inventarios'))
                return

            # Eliminar inventarios existentes si se solicita
            if options['delete']:
                if options['producto'] and options['almacen']:
                    # Eliminar solo los inventarios del producto y almacén especificados
                    count = Inventario.objects.filter(
                        producto__in=productos, almacen__in=almacenes
                    ).count()
                    Inventario.objects.filter(
                        producto__in=productos, almacen__in=almacenes
                    ).delete()
                    self.stdout.write(self.style.WARNING(
                        f'Eliminados {count} inventarios del producto {productos.first().nombre} '
                        f'en el almacén {almacenes.first().nombre}'
                    ))
                elif options['producto']:
                    # Eliminar solo los inventarios del producto especificado
                    count = Inventario.objects.filter(producto__in=productos).count()
                    Inventario.objects.filter(producto__in=productos).delete()
                    self.stdout.write(self.style.WARNING(
                        f'Eliminados {count} inventarios del producto {productos.first().nombre}'
                    ))
                elif options['almacen']:
                    # Eliminar solo los inventarios del almacén especificado
                    count = Inventario.objects.filter(almacen__in=almacenes).count()
                    Inventario.objects.filter(almacen__in=almacenes).delete()
                    self.stdout.write(self.style.WARNING(
                        f'Eliminados {count} inventarios del almacén {almacenes.first().nombre}'
                    ))
                else:
                    # Eliminar todos los inventarios
                    count = Inventario.objects.count()
                    Inventario.objects.all().delete()
                    self.stdout.write(self.style.WARNING(f'Eliminados {count} inventarios existentes'))

            # Generar inventarios
            self.generar_inventarios(productos, almacenes, options['cantidad'])

            # Mostrar resumen
            total_inventarios = Inventario.objects.count()
            self.stdout.write(self.style.SUCCESS(f'Se han generado inventarios exitosamente. Total: {total_inventarios}'))

    def generar_inventarios(self, productos, almacenes, cantidad_total):
        """
        Genera inventarios para los productos y almacenes especificados.
        """
        # Calcular cuántos inventarios generar por producto
        inventarios_por_producto = max(1, cantidad_total // productos.count())

        for producto in productos:
            self.stdout.write(f'Generando inventarios para el producto: {producto.nombre}')

            # Distribuir el producto en diferentes almacenes
            for almacen in almacenes:
                # Obtener ubicaciones del almacén
                ubicaciones = Ubicacion.objects.filter(
                    almacen=almacen,
                    tipo__in=['posicion', 'nivel']  # Solo usar posiciones y niveles
                )

                if not ubicaciones.exists():
                    self.stdout.write(self.style.WARNING(
                        f'  No hay ubicaciones disponibles en el almacén {almacen.nombre}'
                    ))
                    continue

                # Determinar cuántos inventarios generar en este almacén
                inventarios_en_almacen = random.randint(1, min(5, inventarios_por_producto))

                # Seleccionar ubicaciones aleatorias
                ubicaciones_seleccionadas = random.sample(
                    list(ubicaciones),
                    min(inventarios_en_almacen, ubicaciones.count())
                )

                for ubicacion in ubicaciones_seleccionadas:
                    # Generar datos aleatorios para el inventario
                    cantidad = Decimal(str(random.uniform(10, 1000)))
                    cantidad_reservada = Decimal('0')

                    # A veces, añadir una reserva
                    if random.random() < 0.3:  # 30% de probabilidad
                        cantidad_reservada = Decimal(str(random.uniform(0, float(cantidad) / 2)))

                    # Determinar si tiene lote y fecha de vencimiento
                    tiene_lote = random.random() < 0.7  # 70% de probabilidad
                    lote = f"LOT-{random.randint(10000, 99999)}" if tiene_lote else None

                    tiene_vencimiento = tiene_lote and random.random() < 0.8  # 80% de los lotes tienen vencimiento

                    # Generar fecha de vencimiento (entre 1 mes y 2 años en el futuro)
                    fecha_vencimiento = None
                    if tiene_vencimiento:
                        dias_para_vencer = random.randint(-30, 730)  # Algunos ya vencidos
                        fecha_vencimiento = timezone.now().date() + timedelta(days=dias_para_vencer)

                    # Determinar estado del lote
                    estado_lote = EstadoLote.DISPONIBLE
                    if fecha_vencimiento and fecha_vencimiento < timezone.now().date():
                        estado_lote = EstadoLote.VENCIDO
                    elif random.random() < 0.1:  # 10% de probabilidad
                        estado_lote = random.choice([
                            EstadoLote.CUARENTENA, EstadoLote.BLOQUEADO
                        ])

                    # Crear el inventario
                    inventario = Inventario.objects.create(
                        producto=producto,
                        almacen=almacen,
                        ubicacion=ubicacion,
                        lote=lote,
                        fecha_vencimiento=fecha_vencimiento,
                        estado_lote=estado_lote,
                        cantidad=cantidad,
                        cantidad_reservada=cantidad_reservada,
                        costo_unitario=producto.costo * Decimal(str(random.uniform(0.9, 1.1))),
                        notas=f"Inventario de prueba generado automáticamente",
                        fecha_ultimo_movimiento=timezone.now()
                    )

                    # Registrar el movimiento de entrada
                    MovimientoInventario.objects.create(
                        inventario=inventario,
                        tipo='entrada',
                        cantidad=cantidad,
                        es_incremento=True,
                        usuario='sistema',
                        notas="Entrada inicial de inventario (generado automáticamente)"
                    )

                    # Si hay reserva, registrar el movimiento
                    if cantidad_reservada > 0:
                        MovimientoInventario.objects.create(
                            inventario=inventario,
                            tipo='reserva',
                            cantidad=cantidad_reservada,
                            es_incremento=False,
                            usuario='sistema',
                            referencia=f"PED-{random.randint(1000, 9999)}",
                            notas="Reserva automática para pedido de prueba"
                        )

                    self.stdout.write(f"  Inventario creado: {producto.nombre} en {ubicacion.codigo} - {cantidad} unidades")
