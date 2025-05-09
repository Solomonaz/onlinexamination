from django import forms
from django.contrib.auth.models import User
from . import models
from exam import models as QMODEL

from django import forms
from django.contrib.auth.models import User
from . import models

class StudentUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }
        error_messages = {
            'username': {
                'required': "Please enter a username.",
                'unique': "This username is already taken.",
            },
            'password': {
                'required': "Please enter a password.",
            },
        }

class StudentForm(forms.ModelForm):
    class Meta:
        model = models.Student
        fields = ['address', 'mobile', 'course','organization']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
        }


