from django.shortcuts import render,redirect,reverse, get_object_or_404
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from teacher import models as TMODEL
from django.contrib import messages
from datetime import datetime, timedelta
import random
from django.db import IntegrityError

#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')

import random
from django.contrib import messages
from django.db import IntegrityError

def generate_username(first_name):
    """Generate username from first 3 letters of first name + random 3 digits"""
    prefix = first_name[:3].lower()
    while True:
        random_digits = ''.join(random.choice('0123456789') for _ in range(3))
        username = f"{prefix}{random_digits}"
        if not User.objects.filter(username=username).exists():
            return username

def generate_password():
    """Generate 6-digit numeric password"""
    return ''.join(random.choice('0123456789') for _ in range(6))

def student_signup_view(request):
    if request.method == 'POST':
        userForm = forms.StudentUserForm(request.POST)
        studentForm = forms.StudentForm(request.POST, request.FILES)
        
        if userForm.is_valid() and studentForm.is_valid():
            try:
                first_name = userForm.cleaned_data['first_name']
                username = generate_username(first_name)
                password = generate_password()
                
                # Create user with generated credentials
                user = userForm.save(commit=False)
                user.username = username
                user.set_password(password)
                user.save()
                
                # Create student profile
                student = studentForm.save(commit=False)
                student.user = user
                student.save()

                # Add to STUDENT group
                my_student_group = Group.objects.get_or_create(name='STUDENT')
                my_student_group[0].user_set.add(user)

                # Prepare success data
                context = {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': username,
                    'password': password,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d'),
                }
                return render(request, 'student/registration_success.html', context)
                
            except IntegrityError:
                messages.error(request, "Username already exists. Please try again.")
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            for field, errors in userForm.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for field, errors in studentForm.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    # For GET request
    userForm = forms.StudentUserForm()
    studentForm = forms.StudentForm()
    return render(request, 'student/studentsignup.html', {
        'userForm': userForm,
        'studentForm': studentForm,
    })

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()


from django.core.exceptions import ObjectDoesNotExist

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    try:
        student = models.Student.objects.get(user_id=request.user.id)
        student_course = student.course
        total_questions = QMODEL.Question.objects.filter(course=student_course).count()

        context = {
            'total_course': 1,
            'total_question': total_questions,
            'courses': [student_course],
        }

        return render(request, 'student/student_dashboard.html', context=context)
    
    except ObjectDoesNotExist:
        # Handle the case where student doesn't exist
        messages.error(request, "Student profile not found. Please contact administrator.")
        return redirect('studentlogin')


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses=QMODEL.Course.objects.get()
    return render(request,'student/student_exam.html',{'courses':courses})


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)  # Fetch the course by its ID
    questions = QMODEL.Question.objects.all().filter(course=course)
    total_questions = questions.count()
    student = models.Student.objects.get(user_id=request.user.id)
    exam = get_object_or_404(QMODEL.Course, id=pk)
    # result = QMODEL.Result.objects.filter(student=student, exam=exam).first()
    # marks = result.marks

    # Calculate total marks
    total_marks = sum(q.marks for q in questions)

# Check if an attempt record exists
    exam_attempt, created = models.ExamAttempt.objects.get_or_create(
        student=student, 
        course=course,
    )
        # If the exam has already been attempted, don't allow another attempt
    attempted = exam_attempt.attempted
        # If the exam has not been attempted yet, update it
    if not exam_attempt.attempted:
        exam_attempt.attempted = True
        exam_attempt.save()

    context = {
        'course': course,
        'total_questions': total_questions,
        'total_marks': total_marks,
        'attempted': attempted,
        # 'marks' : marks
    }


    return render(request, 'student/take_exam.html', context)


from django.utils import timezone
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request, pk):
    course = QMODEL.Course.objects.get(id=pk)
    given_time = course.given_time

    exam_start_time_str = request.session.get('exam_start_time')
    if not exam_start_time_str:
        exam_start_time = timezone.now()
        exam_start_time_str = exam_start_time.isoformat()
        request.session['exam_start_time'] = exam_start_time_str
    else:
        exam_start_time = timezone.datetime.fromisoformat(exam_start_time_str)

    questions = QMODEL.Question.objects.filter(course=course)

    if request.method == 'POST':
        pass 

    context = {
        'exam_duration_seconds': given_time,
        'exam_start_time': exam_start_time_str,
        'course': course,
        'questions': questions,
    }
    response = render(request, 'student/start_exam.html', context)
    response.set_cookie('course_id', course.id, httponly=True, samesite='Lax')
    return response

# from django.utils import timezone
# import random

# @login_required(login_url='studentlogin')
# @user_passes_test(is_student)
# def start_exam_view(request, pk):
#     course = get_object_or_404(QMODEL.Course, id=pk)
#     given_time = course.given_time

#     # Check if exam has started
#     exam_start_time_str = request.session.get('exam_start_time')
#     if not exam_start_time_str:
#         exam_start_time = timezone.now()
#         exam_start_time_str = exam_start_time.isoformat()
#         request.session['exam_start_time'] = exam_start_time_str
#         request.session['exam_questions'] = None  # Reset questions for new attempt

#     # Get or generate random questions
#     if not request.session.get('exam_questions'):
#         # Use active questions if available, otherwise fall back to random selection
#         if hasattr(course, 'active_questions'):
#             active_questions = list(course.active_questions.filter(is_active=True).values_list('question_id', flat=True))
#             questions = list(QMODEL.Question.objects.filter(id__in=active_questions))
#         else:
#             questions = course.get_random_questions()

#         # Shuffle questions for this student
#         random.shuffle(questions)
#         request.session['exam_questions'] = [q.id for q in questions]
#     else:
#         # Use previously selected questions
#         questions = list(QMODEL.Question.objects.filter(
#             id__in=request.session['exam_questions']
#         ).order_by('?'))


#     context = {
#         'exam_duration_seconds': given_time,
#         'exam_start_time': exam_start_time_str,
#         'course': course,
#         'questions': questions,
#     }
#     response = render(request, 'student/start_exam.html', context)
#     response.set_cookie('course_id', course.id, httponly=True, samesite='Lax')
#     return response

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get('course_id'):
        course_id = request.COOKIES.get('course_id')
        course = QMODEL.Course.objects.get(id=course_id)
        student = models.Student.objects.get(user_id=request.user.id)
        
        total_marks = 0
        questions = QMODEL.Question.objects.filter(course=course)
        
        for i, question in enumerate(questions):
            selected_ans = request.COOKIES.get(str(i+1))
            actual_answer = question.answer
            
            # Create StudentAnswer record for each question
            student_answer, created = QMODEL.StudentAnswer.objects.get_or_create(
                student=student,
                question=question
            )
            
            # Save the student's answer
            student_answer.answer = selected_ans
            
            # Auto-grade if possible (for MCQ/FIB)
            if selected_ans == actual_answer:
                marks_obtained = question.marks
                total_marks += marks_obtained
                student_answer.marks_obtained = marks_obtained
                student_answer.is_graded = True
            
            student_answer.save()
        
        # Save overall result
        result = QMODEL.Result()
        result.marks = total_marks
        result.exam = course
        result.student = student
        result.save()
        
        return HttpResponseRedirect('view-result')



@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    student = models.Student.objects.get(user=request.user)
    student_course = student.course
    # courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':[student_course]})
    

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results= QMODEL.Result.objects.filter(exam=course, student=student)
    # results= QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'student/check_marks.html',{'results':results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})
  
def load_courses(request):
    department_id = request.GET.get('department')
    courses = QMODEL.Course.objects.filter(department_id=department_id)
    return render(request, 'student/course_dropdown_list_options.html', {'courses': courses})
