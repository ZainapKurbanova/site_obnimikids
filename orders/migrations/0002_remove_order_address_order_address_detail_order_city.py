# Generated by Django 5.1.6 on 2025-05-30 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='address',
        ),
        migrations.AddField(
            model_name='order',
            name='address_detail',
            field=models.CharField(default='Не указан', max_length=255, verbose_name='Детальный адрес'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='city',
            field=models.CharField(default='Не указан', max_length=100, verbose_name='Город'),
            preserve_default=False,
        ),
    ]
