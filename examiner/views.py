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
from examiner import models as EMODEL
from django.contrib import messages
import pandas as pd
from io import BytesIO
from django.db.models import Case, When, Value, Sum, Count, IntegerField, Q, F
from django.db.models.functions import Coalesce
from datetime import datetime
from django.db.models import Prefetch
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.core.paginator import Paginator


def get_examiner_department(request):
    examiner = get_object_or_404(models.Examiner, user=request.user)
    return examiner.department

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
                
                my_examiner_group = Group.objects.get_or_create(name='EXAMINER')
                my_examiner_group[0].user_set.add(user)
                
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
    try:
        examiner = EMODEL.Examiner.objects.get(user=request.user)
        assigned_courses = QMODEL.Course.objects.filter(examiners=examiner)
        assigned_courses_count = assigned_courses.count()
        
        # Get pending exams (with ungraded FIB questions)
        pending_exams = QMODEL.Course.objects.filter(
            examiners=examiner
        ).annotate(
            ungraded_fib_count=Count(
                Case(
                    When(questions__question_type='FIB',
                         questions__studentanswer__is_graded=False,
                         then=1),
                    output_field=IntegerField()
                )
            )
        ).filter(ungraded_fib_count__gt=0)
        
        # Get graded exams (all FIB questions graded)
        graded_exams = QMODEL.Course.objects.filter(
            examiners=examiner
        ).annotate(
            total_fib=Count('questions__studentanswer', 
                          filter=Q(questions__question_type='FIB')),
            graded_fib=Count('questions__studentanswer',
                           filter=Q(questions__question_type='FIB', 
                                   questions__studentanswer__is_graded=True))
        ).filter(total_fib__gt=0).exclude(
            total_fib__gt=F('graded_fib')
        )
        
        # Count unseen exams
        unseen_exam_count = QMODEL.Course.objects.filter(
            examiners=examiner,
            is_seen=False
        ).count()

        context = {
            'examiner': examiner,
            'assigned_courses': assigned_courses,
            'assigned_courses_count': assigned_courses_count,
            'unseen_exam_count': unseen_exam_count,
            'pending_exams_count': pending_exams.count(),
            'pending_exams': pending_exams,
            'graded_exams_count': graded_exams.count(),
            'graded_exams': graded_exams,
        }
        return render(request, 'examiner/examiner_dashboard.html', context)
    
    except EMODEL.Examiner.DoesNotExist:
        messages.error(request, "Examiner profile not found.")
        return redirect('examiner:examinerlogin')

        
def examiner_assinged_exam_view(request):
    examiner = EMODEL.Examiner.objects.get(user=request.user)
    courses = QMODEL.Course.objects.filter(examiners=examiner)
    QMODEL.Course.objects.filter(examiners=examiner,is_seen=False).update(is_seen=True)

    context = {
        'courses':courses,
    }
    return render(request, 'examiner/examiner_assigned_exam.html', context)


@login_required(login_url='examiner:examinerlogin')
@user_passes_test(is_examiner)
def examiner_view_examinees_view(request, course_id):
    department = get_examiner_department(request)
    examiner = EMODEL.Examiner.objects.get(user=request.user)
    course = get_object_or_404(QMODEL.Course, id=course_id, examiners=examiner)
    
    # Check if course has FIB questions
    has_fib_questions = QMODEL.Question.objects.filter(
        course=course,
        question_type='FIB'
    ).exists()

    # Base queryset
    results = QMODEL.Result.objects.filter(exam=course).select_related('student')
    
    # Get filter parameters
    organization = request.GET.get('organization', '')
    min_mark = request.GET.get('min_mark', '')
    max_mark = request.GET.get('max_mark', '')
    exam_date = request.GET.get('exam_date', '')

    # Apply filters
    if organization:
        results = results.filter(student__organization=organization)
    if exam_date:
        try:
            date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            results = results.filter(date__date=date_obj)
        except ValueError:
            exam_date = ''

    # Get student data if FIB questions exist
    student_data = {}
    if has_fib_questions:
        fib_data = QMODEL.StudentAnswer.objects.filter(
            question__course=course,
            question__question_type='FIB'
        ).values('student').annotate(
            fib_score=Coalesce(Sum('marks_obtained'), Value(0)),
            total_questions=Count('id'),
            graded_questions=Count(
                Case(
                    When(is_graded=True, then=1),
                    output_field=IntegerField()
                )
            )
        )
        
        student_data = {
            sd['student']: {
                'fib_score': sd['fib_score'],
                'total_questions': sd['total_questions'],
                'graded_questions': sd['graded_questions'],
                'has_fib': True,
                'is_completed': sd['total_questions'] > 0 and sd['total_questions'] == sd['graded_questions']
            }
            for sd in fib_data
        }

    # Prepare results
    results_list = []
    for result in results:
        data = student_data.get(result.student.id, {
            'fib_score': 0,
            'total_questions': 0,
            'graded_questions': 0,
            'has_fib': has_fib_questions,
            'is_completed': False
        })
        
        result.fib_score = data['fib_score']
        result.total_score = result.marks + data['fib_score']
        result.grading_status = {
            'has_fib_questions': has_fib_questions,
            'has_fib_for_student': data['has_fib'],
            'is_completed': data['is_completed'],
            'graded_count': data['graded_questions'],
            'total_questions': data['total_questions']
        }
        results_list.append(result)

    # Apply score filtering
    if min_mark and min_mark.isdigit():
        results_list = [r for r in results_list if r.total_score >= int(min_mark)]
    if max_mark and max_mark.isdigit():
        results_list = [r for r in results_list if r.total_score <= int(max_mark)]

    # Pagination
    paginator = Paginator(results_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'examiner/examiner_view_examinee.html', {
        'course': course,
        'results': page_obj,
        'has_fib_questions': has_fib_questions,
        'organizations': SMODEL.Student.objects.filter(
            department=department
        ).values_list('organization', flat=True).distinct(),
        'selected_org': organization,
        'exam_date': exam_date,
        'min_mark': min_mark,
        'max_mark': max_mark,
    })


def examiner_explanation_grading_view(request, student_id, course_id):
    department = get_examiner_department(request)
    student = get_object_or_404(SMODEL.Student, pk=student_id, department=department)
    examiner = EMODEL.Examiner.objects.get(user=request.user)
    course = get_object_or_404(QMODEL.Course, pk=course_id, department=department)
    
    fib_questions = QMODEL.Question.objects.filter(
        course=course,
        question_type='FIB'
    )
    
    existing_answers = QMODEL.StudentAnswer.objects.filter(
        student=student,
        question__in=fib_questions
    )
    
    answer_map = {a.question_id: a for a in existing_answers}
    questions_answers = []
    total_fib_marks = 0
    current_fib_score = 0
    
    for question in fib_questions:
        answer = answer_map.get(question.id)
        if not answer:
            answer = QMODEL.StudentAnswer.objects.create(
                student=student,
                question=question,
                answer='',
                marks_obtained=0,
                feedback=''
            )
        questions_answers.append((question, answer))
        total_fib_marks += question.marks
        current_fib_score += answer.marks_obtained
    
    if request.method == 'POST':
        new_fib_score = 0
        for question, answer in questions_answers:
            marks_key = f'marks_{question.id}'
            feedback_key = f'feedback_{question.id}'
            
            try:
                marks = min(max(0, int(request.POST.get(marks_key, 0))), question.marks)
                answer.marks_obtained = marks
                new_fib_score += marks
            except ValueError:
                messages.error(request, f"Invalid marks for question {question.id}")
            
            answer.feedback = request.POST.get(feedback_key, '')
            answer.is_graded = True
            answer.save()
        
        messages.success(request, 'FIB grades saved successfully!')
        return redirect(request.META.get('HTTP_REFERER') or 
               reverse('examiner:examiner-view-examinee', args=[course.id]))
    
    # Get submission time from the first answer
    submission_time = questions_answers[0][1].created_at if questions_answers else None
    
    context = {
        'student': student,
        'course': course,
        'questions_answers': questions_answers,
        'submission_time': submission_time,
        'total_fib_marks': total_fib_marks,
        'current_fib_score': current_fib_score
    }
    return render(request, 'examiner/examiner_explanation_grading.html', context)

# def examiner_pending_exam(request):
#     return render(request, 'examiner')