from django.core.management.base import BaseCommand
from django.db import transaction
from almacenes.models import Almacen

class Command(BaseCommand):
    help = 'Genera almacenes de ejemplo para la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Elimina todos los almacenes existentes antes de crear los nuevos',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options['delete']:
                self.stdout.write(self.style.WARNING('Eliminando almacenes existentes...'))
                Almacen.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Almacenes eliminados exitosamente'))

            # Datos de ejemplo
            almacenes_data = [
                {
                    'nombre': 'Almacén Principal',
                    'ubicacion': 'Av. Libertador, Edificio Central, Planta Baja, Caracas',
                    'descripcion': 'Almacén principal con mayor capacidad y productos de alta rotación'
                },
                {
                    'nombre': 'Almacén Norte',
                    'ubicacion': 'Zona Industrial Norte, Galpón 15, Valencia',
                    'descripcion': 'Almacén secundario para distribución en la región central'
                },
                {
                    'nombre': 'Almacén Sur',
                    'ubicacion': 'Calle Principal, Sector Industrial, Maracay',
                    'descripcion': 'Almacén para productos de gran volumen'
                },
                {
                    'nombre': 'Almacén Este',
                    'ubicacion': 'Av. Francisco de Miranda, Centro Comercial El Dorado, Local 25, Petare',
                    'descripcion': 'Almacén para distribución en la zona este de la ciudad'
                },
                {
                    'nombre': 'Almacén Oeste',
                    'ubicacion': 'Carretera Panamericana, Km 15, Galpón 7, Los Teques',
                    'descripcion': 'Almacén para distribución en la zona oeste'
                }
            ]
            
            # Crear almacenes
            almacenes_creados = 0
            
            for data in almacenes_data:
                almacen, created = Almacen.objects.get_or_create(
                    nombre=data['nombre'],
                    defaults={
                        'ubicacion': data['ubicacion'],
                        'descripcion': data['descripcion']
                    }
                )
                
                if created:
                    almacenes_creados += 1
                    self.stdout.write(f"Almacén creado: {almacen.nombre}")
                else:
                    self.stdout.write(f"Almacén ya existente: {almacen.nombre}")
            
            self.stdout.write(self.style.SUCCESS(f'Se han creado {almacenes_creados} almacenes exitosamente'))
