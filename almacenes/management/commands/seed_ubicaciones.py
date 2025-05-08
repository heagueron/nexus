from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
import random
from almacenes.models import Almacen, Ubicacion, TipoUbicacion, UnidadMedidaCapacidad


class Command(BaseCommand):
    help = 'Genera ubicaciones de ejemplo para los almacenes existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Elimina todas las ubicaciones existentes antes de crear las nuevas',
        )
        parser.add_argument(
            '--almacen',
            type=int,
            help='ID del almacén específico para el que generar ubicaciones',
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=50,
            help='Cantidad total aproximada de ubicaciones a generar por almacén',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            # Obtener almacenes
            if options['almacen']:
                almacenes = Almacen.objects.filter(almacen_id=options['almacen'])
                if not almacenes.exists():
                    self.stdout.write(self.style.ERROR(f'No se encontró el almacén con ID {options["almacen"]}'))
                    return
            else:
                almacenes = Almacen.objects.all()
                
            if not almacenes.exists():
                self.stdout.write(self.style.ERROR('No hay almacenes disponibles para generar ubicaciones'))
                return
                
            # Eliminar ubicaciones existentes si se solicita
            if options['delete']:
                if options['almacen']:
                    # Eliminar solo las ubicaciones del almacén especificado
                    count = Ubicacion.objects.filter(almacen__in=almacenes).count()
                    Ubicacion.objects.filter(almacen__in=almacenes).delete()
                    self.stdout.write(self.style.WARNING(f'Eliminadas {count} ubicaciones del almacén {almacenes.first().nombre}'))
                else:
                    # Eliminar todas las ubicaciones
                    count = Ubicacion.objects.count()
                    Ubicacion.objects.all().delete()
                    self.stdout.write(self.style.WARNING(f'Eliminadas {count} ubicaciones existentes'))
            
            # Generar ubicaciones para cada almacén
            for almacen in almacenes:
                self.stdout.write(f'Generando ubicaciones para el almacén: {almacen.nombre}')
                self.generar_ubicaciones_para_almacen(almacen, options['cantidad'])
                
            # Mostrar resumen
            total_ubicaciones = Ubicacion.objects.filter(almacen__in=almacenes).count()
            self.stdout.write(self.style.SUCCESS(f'Se han generado ubicaciones exitosamente. Total: {total_ubicaciones}'))
    
    def generar_ubicaciones_para_almacen(self, almacen, cantidad_total):
        """
        Genera una estructura jerárquica de ubicaciones para un almacén.
        """
        # Definir la estructura jerárquica
        estructura = {
            'zonas': {
                'cantidad': random.randint(2, 4),  # 2-4 zonas por almacén
                'tipo': TipoUbicacion.ZONA,
                'prefijo': 'Z',
                'hijos': {
                    'pasillos': {
                        'cantidad': random.randint(2, 4),  # 2-4 pasillos por zona
                        'tipo': TipoUbicacion.PASILLO,
                        'prefijo': 'P',
                        'hijos': {
                            'estanterias': {
                                'cantidad': random.randint(2, 4),  # 2-4 estanterías por pasillo
                                'tipo': TipoUbicacion.ESTANTERIA,
                                'prefijo': 'E',
                                'hijos': {
                                    'niveles': {
                                        'cantidad': random.randint(3, 5),  # 3-5 niveles por estantería
                                        'tipo': TipoUbicacion.NIVEL,
                                        'prefijo': 'N',
                                        'hijos': {
                                            'posiciones': {
                                                'cantidad': random.randint(4, 8),  # 4-8 posiciones por nivel
                                                'tipo': TipoUbicacion.POSICION,
                                                'prefijo': 'POS',
                                                'hijos': {}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Crear zonas
        for i in range(1, estructura['zonas']['cantidad'] + 1):
            zona = self.crear_ubicacion(
                almacen=almacen,
                codigo=f"{estructura['zonas']['prefijo']}{i:02d}",
                nombre=f"Zona {i}",
                tipo=estructura['zonas']['tipo'],
                padre=None,
                capacidad=None,  # Las zonas no tienen capacidad específica
                unidad_medida=None
            )
            
            # Crear pasillos para esta zona
            self.crear_hijos_recursivamente(
                almacen=almacen,
                padre=zona,
                estructura=estructura['zonas']['hijos'],
                prefijo_codigo=zona.codigo,
                nivel=1
            )
    
    def crear_hijos_recursivamente(self, almacen, padre, estructura, prefijo_codigo, nivel):
        """
        Crea hijos recursivamente según la estructura definida.
        """
        # Obtener el primer nivel de la estructura
        nivel_actual = list(estructura.keys())[0]
        config = estructura[nivel_actual]
        
        # Crear hijos para este nivel
        for i in range(1, config['cantidad'] + 1):
            codigo = f"{prefijo_codigo}-{config['prefijo']}{i:02d}"
            nombre = f"{config['tipo'].capitalize()} {i}"
            
            # Determinar capacidad y unidad de medida según el tipo
            capacidad = None
            unidad_medida = None
            
            if config['tipo'] == TipoUbicacion.ESTANTERIA:
                capacidad = random.randint(500, 2000)
                unidad_medida = UnidadMedidaCapacidad.KILOGRAMO
            elif config['tipo'] == TipoUbicacion.NIVEL:
                capacidad = random.randint(100, 500)
                unidad_medida = UnidadMedidaCapacidad.KILOGRAMO
            elif config['tipo'] == TipoUbicacion.POSICION:
                capacidad = random.randint(20, 100)
                unidad_medida = UnidadMedidaCapacidad.KILOGRAMO
            
            hijo = self.crear_ubicacion(
                almacen=almacen,
                codigo=codigo,
                nombre=nombre,
                tipo=config['tipo'],
                padre=padre,
                capacidad=capacidad,
                unidad_medida=unidad_medida
            )
            
            # Si hay más niveles en la estructura, crear hijos recursivamente
            if config['hijos']:
                self.crear_hijos_recursivamente(
                    almacen=almacen,
                    padre=hijo,
                    estructura=config['hijos'],
                    prefijo_codigo=hijo.codigo,
                    nivel=nivel + 1
                )
    
    def crear_ubicacion(self, almacen, codigo, nombre, tipo, padre, capacidad, unidad_medida):
        """
        Crea una ubicación y la guarda en la base de datos.
        """
        # Verificar si ya existe
        ubicacion_existente = Ubicacion.objects.filter(
            Q(almacen=almacen) & Q(codigo=codigo)
        ).first()
        
        if ubicacion_existente:
            self.stdout.write(f"  Ubicación ya existente: {codigo} - {nombre}")
            return ubicacion_existente
        
        # Crear nueva ubicación
        ubicacion = Ubicacion(
            almacen=almacen,
            codigo=codigo,
            nombre=nombre,
            tipo=tipo,
            padre=padre,
            capacidad=capacidad,
            unidad_medida_capacidad=unidad_medida or UnidadMedidaCapacidad.UNIDAD,
            activa=True,
            descripcion=f"Ubicación {nombre} en {almacen.nombre}"
        )
        ubicacion.save()
        
        self.stdout.write(f"  Ubicación creada: {codigo} - {nombre}")
        return ubicacion
