import random
from django.core.management.base import BaseCommand
from django.db import transaction
from shared_models.models import Cliente

class Command(BaseCommand):
    help = 'Genera 20 clientes de ejemplo para la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Elimina todos los clientes existentes antes de crear los nuevos',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options['delete']:
                self.stdout.write(self.style.WARNING('Eliminando clientes existentes...'))
                Cliente.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Clientes eliminados exitosamente'))

            # Datos de ejemplo
            nombres_juridicos = [
                'Corporación Tecnológica S.A.', 'Distribuidora Comercial C.A.',
                'Inversiones Futuro C.A.', 'Importadora Global S.A.',
                'Servicios Profesionales S.R.L.', 'Consultores Asociados C.A.',
                'Manufacturas Industriales S.A.', 'Soluciones Empresariales C.A.',
                'Comercializadora Internacional S.A.', 'Grupo Financiero C.A.'
            ]
            
            nombres_naturales = [
                'Juan Pérez', 'María González', 'Carlos Rodríguez',
                'Ana Martínez', 'Luis Hernández', 'Carmen López',
                'Pedro Sánchez', 'Laura Díaz', 'Miguel Torres',
                'Sofía Ramírez'
            ]
            
            direcciones = [
                'Av. Principal, Edificio Centro, Piso 5, Oficina 503',
                'Calle Los Robles, Residencia El Bosque, Apto. 12-B',
                'Urbanización Las Mercedes, Calle 4, Casa 27',
                'Centro Comercial Plaza, Local 45, Nivel PB',
                'Av. Libertador, Edificio Libertador, Piso 10, Oficina 10-C',
                'Calle El Recreo, Quinta Santa Mónica',
                'Av. Francisco de Miranda, Centro Plaza, Torre A, Piso 8',
                'Urbanización Santa Fe, Calle Principal, Casa 15',
                'Av. Las Américas, Centro Empresarial, Torre Norte, Piso 3',
                'Calle La Paz, Residencias La Arboleda, Apto. 5-A'
            ]
            
            ciudades = ['Caracas', 'Valencia', 'Maracaibo', 'Barquisimeto', 'Maracay']
            
            # Crear 20 clientes (10 jurídicos y 10 naturales)
            clientes_creados = 0
            
            # Crear clientes jurídicos
            for i in range(10):
                # Generar datos para cliente jurídico
                nombre = nombres_juridicos[i] if i < len(nombres_juridicos) else f"Empresa {i+1} C.A."
                rif = f"J{random.randint(10000000, 99999999)}9"
                email = f"contacto@{nombre.lower().replace(' ', '').replace(',', '').replace('.', '')}.com"
                direccion = random.choice(direcciones)
                telefono = f"+58 212 {random.randint(1000000, 9999999)}"
                nombre_contacto = random.choice(nombres_naturales)
                telefono_contacto = f"+58 412 {random.randint(1000000, 9999999)}"
                comentario = "Cliente corporativo" if random.choice([True, False]) else ""
                
                # Crear el cliente
                cliente = Cliente.objects.create(
                    tipo="juridico",
                    rif=rif,
                    nombre=nombre,
                    email=email,
                    pais="Venezuela",
                    direccion=direccion,
                    telefono=telefono,
                    nombre_contacto=nombre_contacto,
                    telefono_contacto=telefono_contacto,
                    comentario=comentario
                )
                
                clientes_creados += 1
                self.stdout.write(f"Cliente jurídico creado: {cliente.nombre} ({cliente.rif})")
            
            # Crear clientes naturales
            for i in range(10):
                # Generar datos para cliente natural
                nombre = nombres_naturales[i] if i < len(nombres_naturales) else f"Cliente Natural {i+1}"
                rif = f"V{random.randint(10000000, 99999999)}9"
                email = f"{nombre.lower().replace(' ', '.')}@email.com"
                direccion = random.choice(direcciones)
                telefono = f"+58 {random.choice(['412', '414', '424'])} {random.randint(1000000, 9999999)}"
                ciudad = random.choice(ciudades)
                comentario = "Cliente frecuente" if random.choice([True, False]) else ""
                
                # Crear el cliente
                cliente = Cliente.objects.create(
                    tipo="natural",
                    rif=rif,
                    nombre=nombre,
                    email=email,
                    pais="Venezuela",
                    direccion=direccion,
                    telefono=telefono,
                    comentario=comentario
                )
                
                clientes_creados += 1
                self.stdout.write(f"Cliente natural creado: {cliente.nombre} ({cliente.rif})")
            
            self.stdout.write(self.style.SUCCESS(f'Se han creado {clientes_creados} clientes exitosamente'))
