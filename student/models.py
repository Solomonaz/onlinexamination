from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
   
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_instance(self):
        return self
    def __str__(self):
        return self.user.first_name

class ExamAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)  # Assuming the student is a User
    course = models.ForeignKey('exam.Course', on_delete=models.CASCADE)
    attempt_time = models.DateTimeField(auto_now_add=True)  # Records when the student took the exam
    attempted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('student', 'course')  # Prevent multiple attempts by the same student on the same exam


