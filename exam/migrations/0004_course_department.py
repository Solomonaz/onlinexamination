# Generated by Django 3.0.5 on 2025-05-17 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0003_auto_20250517_1732'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='department',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='exam.Department'),
            preserve_default=False,
        ),
    ]
