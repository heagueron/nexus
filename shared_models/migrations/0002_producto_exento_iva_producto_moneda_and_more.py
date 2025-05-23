# Generated by Django 5.2 on 2025-05-07 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shared_models', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='exento_iva',
            field=models.BooleanField(default=False, verbose_name='Exento de IVA'),
        ),
        migrations.AddField(
            model_name='producto',
            name='moneda',
            field=models.CharField(choices=[('Bolivares', 'Bolívares'), ('USD', 'Dólares Estadounidenses')], default='Bolivares', max_length=10, verbose_name='Moneda'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='descripcion',
            field=models.TextField(verbose_name='Descripción'),
        ),
    ]
