import random
from django.core.management.base import BaseCommand
from django.db import transaction
from shared_models.models import Producto

class Command(BaseCommand):
    help = 'Genera 20 productos de ejemplo para la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Elimina todos los productos existentes antes de crear los nuevos',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options['delete']:
                self.stdout.write(self.style.WARNING('Eliminando productos existentes...'))
                Producto.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Productos eliminados exitosamente'))

            # Datos de ejemplo
            nombres_productos = [
                'Laptop HP Pavilion', 'Monitor Dell 24"', 'Teclado Logitech K380',
                'Mouse Inalámbrico Microsoft', 'Impresora Epson L3150', 'Disco Duro Externo 1TB',
                'Memoria USB 64GB', 'Audífonos Sony WH-1000XM4', 'Cámara Web Logitech C920',
                'Router TP-Link Archer C6', 'Tablet Samsung Galaxy Tab A7', 'Smartphone Xiaomi Redmi Note 10',
                'Smart TV LG 43"', 'Consola PlayStation 5', 'Altavoces Bluetooth JBL Flip 5',
                'Batería Externa 10000mAh', 'Adaptador HDMI a VGA', 'Tarjeta MicroSD 128GB',
                'Estuche para Laptop', 'Regleta de Enchufes'
            ]
            
            marcas = ['HP', 'Dell', 'Logitech', 'Microsoft', 'Epson', 'Samsung', 'Sony', 
                     'TP-Link', 'Xiaomi', 'LG', 'JBL', 'Kingston', 'SanDisk', 'Belkin']
            
            descripciones = [
                'Producto de alta calidad con garantía extendida',
                'Ideal para uso profesional y personal',
                'Diseño ergonómico y moderno',
                'Tecnología de última generación',
                'Excelente relación calidad-precio',
                'Compatible con múltiples dispositivos',
                'Incluye accesorios adicionales',
                'Resistente y duradero',
                'Bajo consumo energético',
                'Fácil instalación y configuración'
            ]
            
            unidades_medida = ['unidades', 'Kg', 'Cajas', 'Lts']
            monedas = ['Bolivares', 'USD']
            
            # Crear 20 productos
            productos_creados = 0
            
            for i in range(20):
                # Generar datos aleatorios para cada producto
                nombre = nombres_productos[i] if i < len(nombres_productos) else f"Producto {i+1}"
                marca = random.choice(marcas)
                descripcion = random.choice(descripciones)
                codigo = f"PROD-{i+1:03d}"
                moneda = random.choice(monedas)
                precio_base = random.uniform(10, 1000)
                precio_venta = round(precio_base, 2)
                costo = round(precio_base * 0.7, 2)  # Costo es 70% del precio de venta
                unidad_medida = random.choice(unidades_medida)
                stock = random.randint(5, 100)
                alerta_stock = random.randint(1, 5)
                exento_iva = random.choice([True, False])
                
                # Crear el producto
                producto = Producto.objects.create(
                    nombre=nombre,
                    marca=marca,
                    descripcion=descripcion,
                    codigo=codigo,
                    moneda=moneda,
                    precio_venta=precio_venta,
                    costo=costo,
                    unidad_medida=unidad_medida,
                    stock=stock,
                    alerta_stock=alerta_stock,
                    exento_iva=exento_iva
                )
                
                productos_creados += 1
                self.stdout.write(f"Producto creado: {producto.nombre} ({producto.codigo})")
            
            self.stdout.write(self.style.SUCCESS(f'Se han creado {productos_creados} productos exitosamente'))
