# Generated by Django 5.2 on 2025-05-08 17:23

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shared_models', '0007_alter_moneda_nombre_alter_producto_moneda'),
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('empresa_id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID de la Empresa')),
                ('nombre_legal', models.CharField(help_text='Nombre legal completo de la empresa', max_length=100, verbose_name='Nombre Legal')),
                ('nombre_comercial', models.CharField(help_text='Nombre comercial o marca de la empresa', max_length=100, verbose_name='Nombre Comercial')),
                ('rif', models.CharField(help_text='Registro de Información Fiscal', max_length=10, validators=[django.core.validators.RegexValidator(message='El RIF debe tener el formato: J/V/G seguido de 9 dígitos.', regex='^[JVG][0-9]{9}$')], verbose_name='RIF')),
                ('logo', models.ImageField(blank=True, help_text='Logotipo de la empresa', null=True, upload_to='empresa/logos/', verbose_name='Logo')),
                ('es_activa', models.BooleanField(default=True, help_text='Indica si la empresa está activa', verbose_name='Activa')),
                ('direccion_fiscal', models.TextField(help_text='Dirección fiscal completa', verbose_name='Dirección Fiscal')),
                ('ciudad', models.CharField(help_text='Ciudad de la sede principal', max_length=50, verbose_name='Ciudad')),
                ('estado', models.CharField(help_text='Estado o provincia', max_length=50, verbose_name='Estado/Provincia')),
                ('pais', models.CharField(default='Venezuela', help_text='País de registro', max_length=50, verbose_name='País')),
                ('codigo_postal', models.CharField(blank=True, help_text='Código postal', max_length=10, null=True, verbose_name='Código Postal')),
                ('telefono', models.CharField(blank=True, help_text='Teléfono principal', max_length=20, null=True, verbose_name='Teléfono')),
                ('email', models.EmailField(blank=True, help_text='Email corporativo', max_length=254, null=True, verbose_name='Email')),
                ('sitio_web', models.URLField(blank=True, help_text='Sitio web de la empresa', null=True, verbose_name='Sitio Web')),
                ('porcentaje_iva', models.DecimalField(decimal_places=2, default=16.0, help_text='Porcentaje de IVA estándar', max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Porcentaje de IVA')),
                ('aplica_retenciones', models.BooleanField(default=True, help_text='Indica si la empresa aplica retenciones', verbose_name='Aplica Retenciones')),
                ('formato_factura', models.CharField(default='FAC-{year}{month}-{sequence:04d}', help_text='Formato para numeración de facturas', max_length=50, verbose_name='Formato de Factura')),
                ('formato_orden_compra', models.CharField(default='OC-{year}{month}-{sequence:04d}', help_text='Formato para numeración de órdenes de compra', max_length=50, verbose_name='Formato de Orden de Compra')),
                ('dias_alerta_vencimiento', models.PositiveIntegerField(default=30, help_text='Días para alertar sobre vencimientos', verbose_name='Días Alerta Vencimiento')),
                ('configuracion_adicional', models.JSONField(blank=True, help_text='Configuraciones adicionales en formato JSON', null=True, verbose_name='Configuración Adicional')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
                ('moneda_base', models.ForeignKey(blank=True, help_text='Moneda base para la empresa', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='empresa_moneda_base', to='shared_models.moneda', verbose_name='Moneda Base')),
            ],
            options={
                'verbose_name': 'Empresa',
                'verbose_name_plural': 'Empresas',
            },
        ),
    ]
