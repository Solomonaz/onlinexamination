# Generated by Django 3.2.6 on 2025-04-15 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0002_teacher_salary'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='department',
            field=models.CharField(default='computer', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='teacher',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
