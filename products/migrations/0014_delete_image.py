# Generated by Django 4.0.7 on 2022-09-06 16:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_delete_category'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Image',
        ),
    ]