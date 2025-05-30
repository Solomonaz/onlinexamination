# Generated by Django 4.2.20 on 2025-05-19 10:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0005_alter_activequestion_id_alter_course_department_and_more'),
        ('teacher', '0002_auto_20250517_1905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teachers', to='exam.department'),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
