from django.db import models
from django.contrib.auth.models import User

class Examiner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)
    
    department = models.ForeignKey(
        'exam.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='examiners'
    )
    
    @property 
    def role(self):
        return "Examiner"

    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_instance(self):
        return self
    def __str__(self):
        return self.user.first_name