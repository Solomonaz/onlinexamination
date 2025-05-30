# Generated by Django 3.0.5 on 2025-05-17 13:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('student', '0001_initial'),
        ('exam', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentanswer',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.Student'),
        ),
        migrations.AddField(
            model_name='result',
            name='exam',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.Course'),
        ),
        migrations.AddField(
            model_name='result',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.Student'),
        ),
        migrations.AddField(
            model_name='question',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='exam.Course'),
        ),
        migrations.AddField(
            model_name='activequestion',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='active_questions', to='exam.Course'),
        ),
        migrations.AddField(
            model_name='activequestion',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.Question'),
        ),
        migrations.AlterUniqueTogether(
            name='studentanswer',
            unique_together={('student', 'question')},
        ),
        migrations.AlterUniqueTogether(
            name='activequestion',
            unique_together={('course', 'question')},
        ),
    ]
