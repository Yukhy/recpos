# Generated by Django 3.2.8 on 2021-11-09 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='alias',
            field=models.EmailField(blank=True, default='', max_length=50),
        ),
    ]
