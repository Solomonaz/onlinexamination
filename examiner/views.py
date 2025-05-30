from django.shortcuts import render
from . import forms
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages

def examiner_signup_view(request):
    if request.method == 'POST':
        userForm = forms.ExaminerUserForm(request.POST)
        examinerForm = forms.ExaminerForm(request.POST, request.FILES)
        
        if userForm.is_valid() and examinerForm.is_valid():
            try:
                user = userForm.save(commit=False)
                user.set_password(user.password)
                user.save()
                
                examiner = examinerForm.save(commit=False)
                examiner.user = user
                examiner.save()
                
                my_teacher_group = Group.objects.get_or_create(name='TEACHER')
                my_teacher_group[0].user_set.add(user)
                
                messages.success(request, 'Trainer account created successfully!')
                return HttpResponseRedirect('examinersignup')
            
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        else:
            # Form validation failed
            error_messages = []
            for field, errors in userForm.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            for field, errors in examinerForm.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            for msg in error_messages:
                messages.error(request, msg)
    
    else:
        userForm = forms.ExaminerUserForm()
        examinerForm = forms.ExaminerForm()
    
    return render(request, 'examiner/examinersignup.html', {
        'userForm': userForm,
        'examinerForm': examinerForm
    })


def is_examiner(user):
    return user.groups.filter(name='EXAMINER').exists()
