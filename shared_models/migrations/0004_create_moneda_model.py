# Generated by Django 5.2 on 2025-05-08 14:04

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('shared_models', '0003_cliente'),
    ]

    operations = [
        migrations.CreateModel(
            name='Moneda',
            fields=[
                ('moneda_id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID de la Moneda')),
                ('nombre', models.CharField(max_length=50, unique=True, verbose_name='Nombre')),
                ('simbolo', models.CharField(max_length=10, verbose_name='Símbolo')),
                ('es_base', models.BooleanField(default=False, help_text='Indica si esta es la moneda base del sistema. Solo una moneda puede ser la base.', verbose_name='Es moneda base')),
                ('tasa_oficial', models.DecimalField(decimal_places=8, help_text='Tasa de cambio oficial con respecto a la moneda base', max_digits=20, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Tasa Oficial')),
                ('tasa_mercado', models.DecimalField(decimal_places=8, help_text='Tasa de cambio del mercado con respecto a la moneda base', max_digits=20, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Tasa de Mercado')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
            ],
            options={
                'verbose_name': 'Moneda',
                'verbose_name_plural': 'Monedas',
                'ordering': ['nombre'],
            },
        ),
    ]
