from django import forms
from django.contrib.auth.models import User
from . import models
from django.core.exceptions import ValidationError


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
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another one.")
        return username
    

from exam import models as QMODEL
class TeacherForm(forms.ModelForm):
    class Meta:
        model = models.Teacher
        fields = ['address', 'mobile', 'department']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = QMODEL.Department.objects.all()
        self.fields['department'].required = True  # Make it required at form level
        self.fields['department'].widget.attrs.update({
            'class': 'form-control',
            'id': 'id_department'
        })

