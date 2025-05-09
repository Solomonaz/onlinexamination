from django import forms
from django.contrib.auth.models import User
from . import models

class TeacherUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
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

class TeacherForm(forms.ModelForm):
    class Meta:
        model=models.Teacher
        fields=['address','mobile', 'department']

