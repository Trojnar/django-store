# Generated by Django 4.0.6 on 2022-08-26 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_product_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='count',
            field=models.IntegerField(default=0),
        ),
    ]
