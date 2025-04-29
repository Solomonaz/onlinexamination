from django.db import models
from django.contrib.auth.models import User
from django.apps import apps


class Student(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    organization = models.CharField(max_length=200, null=False)
    
    def get_course_model():
        return apps.get_model('exam', 'Course')

    course = models.ForeignKey(
        'exam.Course',
        on_delete=models.SET_NULL,
        null=True
    )
   
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_instance(self):
        return self
    def __str__(self):
        return self.user.first_name

class ExamAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey('exam.Course', on_delete=models.CASCADE)
    attempt_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    attempted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)  

    class Meta:
        unique_together = ('student', 'course')
