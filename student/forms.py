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
        fields = ['address', 'mobile', 'course','organization','department']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can customize the queryset for department if needed
        self.fields['department'].queryset = QMODEL.Department.objects.all()
        self.fields['course'].queryset = QMODEL.Course.objects.none()

        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['course'].queryset = QMODEL.Course.objects.filter(department_id=department_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.department:
            self.fields['course'].queryset = self.instance.department.course_set.all()


