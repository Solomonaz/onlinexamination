from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from student import models as SMODEL
from exam import forms as QFORM
from django.contrib import messages
import pandas as pd
from io import BytesIO
import csv

#for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'teacher/teacherclick.html')

def teacher_signup_view(request):
    userForm=forms.TeacherUserForm()
    teacherForm=forms.TeacherForm()
    mydict={'userForm':userForm,'teacherForm':teacherForm}
    if request.method=='POST':
        userForm=forms.TeacherUserForm(request.POST)
        teacherForm=forms.TeacherForm(request.POST,request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            teacher=teacherForm.save(commit=False)
            teacher.user=user
            teacher.save()
            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)
        return HttpResponseRedirect('teachersignup')
    return render(request,'teacher/teachersignup.html',context=mydict)



def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    'total_student':SMODEL.Student.objects.all().count()
    }
    return render(request,'teacher/teacher_dashboard.html',context=dict)

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request,'teacher/teacher_exam.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    courseForm=QFORM.CourseForm()
    if request.method=='POST':
        courseForm=QFORM.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/teacher/teacher-view-exam')
    return render(request,'teacher/teacher_add_exam.html',{'courseForm':courseForm})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request,'teacher/teacher_view_exam.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def delete_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/teacher/teacher-view-exam')

@login_required(login_url='adminlogin')
def teacher_question_view(request):
    return render(request,'teacher/teacher_question.html')

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_add_question_view(request):
#     questionForm=QFORM.QuestionForm()
#     if request.method=='POST':
#         questionForm=QFORM.QuestionForm(request.POST)
#         if questionForm.is_valid():
#             question=questionForm.save(commit=False)
#             course=QMODEL.Course.objects.get(id=request.POST.get('courseID'))
#             question.course=course
#             question.save()       
#         else:
#             print("form is invalid")
#         return HttpResponseRedirect('/teacher/teacher-view-question')
#     return render(request,'teacher/teacher_add_question.html',{'questionForm':questionForm})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    questionForm = QFORM.QuestionForm()
    
    if request.method == 'POST':
        # Check if it's a file import
        if 'question_file' in request.FILES:
            return handle_bulk_import(request)
        else:
            # Handle single question form submission
            questionForm = QFORM.QuestionForm(request.POST)
            if questionForm.is_valid():
                question = questionForm.save(commit=False)
                course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
                question.course = course
                question.save()
                messages.success(request, "Question added successfully!")
            else:
                messages.error(request, "Form is invalid. Please check your inputs.")
            return HttpResponseRedirect('/teacher/teacher-add-question')
    
    return render(request, 'teacher/teacher_add_question.html', {'questionForm': questionForm})

def handle_bulk_import(request):
    try:
        course_id = request.POST.get('courseID')
        course = QMODEL.Course.objects.get(id=course_id)
        file = request.FILES['question_file']
        
        # Determine file type and read accordingly
        if file.name.endswith('.csv'):
            df = pd.read_csv(BytesIO(file.read()))
        else:  # Assume Excel
            df = pd.read_excel(BytesIO(file.read()))
        
        success_count = 0
        error_messages = []
        
        for index, row in df.iterrows():
            try:
                # Validate required fields
                required_fields = ['question', 'marks', 'option1', 'option2', 'option3', 'option4', 'answer']
                if not all(field in row for field in required_fields):
                    raise ValueError("Missing required columns in the file")
                
                # Create question
                QMODEL.Question.objects.create(
                    course=course,
                    question=row['question'],
                    marks=int(row['marks']),
                    option1=row['option1'],
                    option2=row['option2'],
                    option3=row['option3'],
                    option4=row['option4'],
                    answer=f"Option{row['answer']}" if str(row['answer']).isdigit() else row['answer']
                )
                success_count += 1
                
            except Exception as e:
                error_messages.append(f"Row {index+2}: {str(e)}")
        
        if success_count > 0:
            messages.success(request, f"Successfully imported {success_count} questions!")
        if error_messages:
            messages.warning(request, f"Completed with {len(error_messages)} errors")
            # Store errors in session to display on next page
            request.session['import_errors'] = error_messages
        
        return HttpResponseRedirect('/teacher/teacher-add-question')
    
    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
        return HttpResponseRedirect('/teacher/teacher-add-question')

def download_question_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_import_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['question', 'marks', 'option1', 'option2', 'option3', 'option4', 'answer'])
    writer.writerow(['Sample question text?', '5', 'Option 1 text', 'Option 2 text', 'Option 3 text', 'Option 4 text', '1'])
    
    return response


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    courses= QMODEL.Course.objects.all()
    return render(request,'teacher/teacher_view_question.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request,pk):
    questions=QMODEL.Question.objects.all().filter(course_id=pk)
    return render(request,'teacher/see_question.html',{'questions':questions})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request,pk):
    question=QMODEL.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def update_question_view(request, pk):
#     question = QMODEL.Question.objects.get(id=pk)
#     questionForm = QFORM.QuestionForm(instance=question)
    
#     if request.method == 'POST':
#         questionForm = QFORM.QuestionForm(request.POST, instance=question)
#         if questionForm.is_valid():
#             question = questionForm.save(commit=False)
#             course = QMODEL.Course.objects.get(id=request.POST.get('course'))
#             question.course = course
#             question.save()       
#             messages.success(request, "Question updated successfully!")
#             return HttpResponseRedirect('/teacher/teacher-view-question')
#         else:
#             messages.error(request, "Error updating question. Please check your inputs.")
    
#     return HttpResponseRedirect('/teacher/teacher-view-question')
