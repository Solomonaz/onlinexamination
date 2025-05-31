from django.shortcuts import render, redirect, reverse, get_object_or_404
from . import forms, models
from django.db.models import Sum, Count
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from student import models as SMODEL
from exam import forms as QFORM
from django.contrib import messages
import pandas as pd
from io import BytesIO
import csv
from datetime import datetime
from django.db.models import Prefetch
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def examinerclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'examiner/examinerclick.html')



class ExaminerLoginView(LoginView):
    template_name = 'examiner/examinerlogin.html'
    
    def form_valid(self, form):
        user = form.get_user()
        print(f"User groups: {user.groups.all()}")  # Check console for output
        if not is_examiner(user):
            print("User is not an examiner")
            messages.error(self.request, 'You are not registered as an examiner')
            return redirect('examiner:examinerlogin')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('examiner:examiner-dashboard')

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
                
                my_teacher_group = Group.objects.get_or_create(name='EXAMINER')
                my_teacher_group[0].user_set.add(user)
                
                messages.success(request, 'Examiner account created successfully!')
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

@login_required(login_url='examiner:examinerlogin')
@user_passes_test(is_examiner)
def examiner_dashboard_view(request):
    context = {
        'total_course': QMODEL.Course.objects.all(),
    }
    return render(request,'examiner/examiner_dashboard.html', context)
