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

# Helper function to get teacher's department
def get_teacher_department(request):
    teacher = get_object_or_404(models.Teacher, user=request.user)
    return teacher.department

#for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'teacher/teacherclick.html')

from django.contrib import messages

def teacher_signup_view(request):
    if request.method == 'POST':
        userForm = forms.TeacherUserForm(request.POST)
        teacherForm = forms.TeacherForm(request.POST, request.FILES)
        
        if userForm.is_valid() and teacherForm.is_valid():
            try:
                user = userForm.save(commit=False)
                user.set_password(user.password)
                user.save()
                
                teacher = teacherForm.save(commit=False)
                teacher.user = user
                teacher.save()
                
                my_teacher_group = Group.objects.get_or_create(name='TEACHER')
                my_teacher_group[0].user_set.add(user)
                
                messages.success(request, 'Trainer account created successfully!')
                return HttpResponseRedirect('teachersignup')
            
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        else:
            # Form validation failed
            error_messages = []
            for field, errors in userForm.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            for field, errors in teacherForm.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            for msg in error_messages:
                messages.error(request, msg)
    
    else:
        userForm = forms.TeacherUserForm()
        teacherForm = forms.TeacherForm()
    
    return render(request, 'teacher/teachersignup.html', {
        'userForm': userForm,
        'teacherForm': teacherForm
    })

def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    department = get_teacher_department(request)
    
    # Get all counts in optimized way
    context = {
        'total_course': QMODEL.Course.objects.filter(department=department).count(),
        'total_question': QMODEL.Question.objects.filter(course__department=department).count(),
        'total_student': SMODEL.Student.objects.filter(department=department).count(),
        'department': department
    }
    return render(request,'teacher/teacher_dashboard.html', context)

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request,'teacher/teacher_exam.html')


@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    department = get_teacher_department(request)
    
    if request.method == 'POST':
        courseForm = QFORM.CourseForm(request.POST, department=department)
        if courseForm.is_valid():        
            course = courseForm.save()  # Department will be set automatically
            messages.success(request, "Course added successfully!")
            return redirect('teacher:teacher-view-exam')
    else:
        courseForm = QFORM.CourseForm(department=department)
    
    return render(request,'teacher/teacher_add_exam.html',{'courseForm':courseForm})

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    department = get_teacher_department(request)
    courses = QMODEL.Course.objects.filter(department=department)
    return render(request,'teacher/teacher_view_exam.html',{'courses':courses})

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def delete_exam_view(request,pk):
    department = get_teacher_department(request)
    course = get_object_or_404(QMODEL.Course, id=pk, department=department)
    course.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect('teacher:teacher-view-exam')

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_question_view(request):
    return render(request,'teacher/teacher_question.html')


@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    # Get teacher's department
    teacher = models.Teacher.objects.get(user=request.user)
    department = teacher.department
    
    if request.method == 'POST':
        if 'question_file' in request.FILES:
            return handle_bulk_import(request)
        else:
            questionForm = QFORM.QuestionForm(request.POST, department=department)
            if questionForm.is_valid():
                question = questionForm.save()
                messages.success(request, f"{question.get_question_type_display()} question added successfully!")
                return redirect('teacher:teacher-add-question')
            else:
                messages.error(request, "Form is invalid. Please check your inputs.")
    else:
        questionForm = QFORM.QuestionForm(department=department)
    
    return render(request, 'teacher/teacher_add_question.html', {
        'questionForm': questionForm,
        'import_errors': request.session.pop('import_errors', None)
    })

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def handle_bulk_import(request):
    teacher = models.Teacher.objects.get(user=request.user)
    department = teacher.department

    try:
        course_id = request.POST.get('courseID')
        import_type = request.POST.get('import_type', 'MCQ')

        try:
            course = QMODEL.Course.objects.get(id=course_id, department=department)
        except QMODEL.Course.DoesNotExist:
            messages.error(request, "Invalid course selection or you don't have permission to add questions to this course.")
            return redirect('teacher:teacher-add-question')

        if 'question_file' not in request.FILES:
            messages.error(request, "No file was uploaded.")
            return redirect('teacher:teacher-add-question')

        file = request.FILES['question_file']

        # Attempt to read CSV or Excel with fallback encoding
        try:
            if file.name.endswith('.csv'):
                try:
                    df = pd.read_csv(BytesIO(file.read()), encoding='utf-8')
                except UnicodeDecodeError:
                    file.seek(0)
                    df = pd.read_csv(BytesIO(file.read()), encoding='cp1252')
            else:
                df = pd.read_excel(BytesIO(file.read()))
        except Exception as e:
            messages.error(request, f"Error reading file: {str(e)}")
            return redirect('teacher:teacher-add-question')

        success_count = 0
        error_messages = []

        for index, row in df.iterrows():
            try:
                if import_type == 'MCQ':
                    required_fields = ['question', 'marks', 'option1', 'option2', 'answer']
                    if not all(field in row.index for field in required_fields):
                        raise ValueError("Missing required columns for MCQ import.")

                    QMODEL.Question.objects.create(
                        course=course,
                        question_type='MCQ',
                        question=row['question'],
                        marks=int(row['marks']),
                        option1=row['option1'],
                        option2=row['option2'],
                        option3=row.get('option3', ''),
                        option4=row.get('option4', ''),
                        answer=f"Option{row['answer']}" if str(row['answer']).isdigit() else row['answer'],
                    )

                elif import_type == 'FIB':
                    required_fields = ['question_text', 'marks', 'blank_answer']
                    if not all(field in row.index for field in required_fields):
                        raise ValueError("Missing required columns for FIB import.")

                    QMODEL.Question.objects.create(
                        course=course,
                        question_type='FIB',
                        question=row['question_text'],
                        marks=int(row['marks']),
                        blank_answer=row['blank_answer'],
                        case_sensitive=str(row.get('case_sensitive', 'false')).lower() == 'true',
                    )

                success_count += 1

            except Exception as e:
                error_messages.append(f"Row {index+2}: {str(e)}")

        if success_count > 0:
            messages.success(request, f"Successfully imported {success_count} {import_type} questions!")
        if error_messages:
            messages.warning(request, f"Completed with {len(error_messages)} errors.")
            request.session['import_errors'] = error_messages

    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")

    return redirect('teacher:teacher-add-question')
    
@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def download_question_template(request, type):
    response = HttpResponse(content_type='text/csv')
    
    if type == 'mcq':
        response['Content-Disposition'] = 'attachment; filename="mcq_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(['question', 'marks', 'option1', 'option2', 'option3', 'option4', 'answer'])
        writer.writerow(['What is 2+2?', '2', '3', '4', '5', '6', 'Option2'])
    elif type == 'fib':
        response['Content-Disposition'] = 'attachment; filename="fib_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(['question_text', 'marks', 'blank_answer', 'case_sensitive'])
        writer.writerow(['The capital of France is _____.', '2', 'Paris', 'false'])
    
    return response

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    department = get_teacher_department(request)
    courses = QMODEL.Course.objects.filter(department=department)
    return render(request,'teacher/teacher_view_question.html',{'courses':courses})

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request,pk):
    department = get_teacher_department(request)
    course = get_object_or_404(QMODEL.Course, id=pk, department=department)
    questions = QMODEL.Question.objects.filter(course=course)
    return render(request,'teacher/see_question.html',{
        'questions': questions,
        'course': course
    })

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request,pk):
    department = get_teacher_department(request)
    question = get_object_or_404(QMODEL.Question, id=pk, course__department=department)
    question.delete()
    messages.success(request, "Question deleted successfully!")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_examinees_view(request, course_id):
    department = get_teacher_department(request)
    course = get_object_or_404(QMODEL.Course, id=course_id, department=department)
    
    results = QMODEL.Result.objects.filter(exam=course).select_related('student')
    
    student_ids = [result.student.id for result in results]
    fib_answers = QMODEL.StudentAnswer.objects.filter(
        student_id__in=student_ids,
        question__course=course,
        question__question_type='FIB'
    ).values('student').annotate(fib_score=Sum('marks_obtained'))
    
    fib_scores = {answer['student']: answer['fib_score'] or 0 for answer in fib_answers}
    
    for result in results:
        result.fib_score = fib_scores.get(result.student.id, 0)
        result.total_score = result.marks + result.fib_score
    
    # Apply filters
    organization = request.GET.get('organization', '')
    min_mark = request.GET.get('min_mark', '')
    max_mark = request.GET.get('max_mark', '')
    exam_date = request.GET.get('exam_date', '')

    if organization:
        results = results.filter(student__organization=organization)
    if min_mark and min_mark.isdigit():
        results = results.filter(marks__gte=int(min_mark))
    if max_mark and max_mark.isdigit():
        results = results.filter(marks__lte=int(max_mark))
    if exam_date:
        try:
            date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            results = results.filter(date__date=date_obj)
        except ValueError:
            exam_date = ''

    organizations = SMODEL.Student.objects.filter(
        department=department
    ).values_list('organization', flat=True).distinct()
    
    return render(request, 'teacher/teacher_view_examinee.html', {        
        'course': course,
        'results': results,
        'organizations': organizations,
        'selected_org': organization,
        'exam_date': exam_date,
        'min_mark': min_mark,
        'max_mark': max_mark,
    })

@login_required(login_url='teacher:teacherlogin')
@user_passes_test(is_teacher)
def teacher_explanation_grading_view(request, student_id, course_id):
    department = get_teacher_department(request)
    student = get_object_or_404(SMODEL.Student, pk=student_id, department=department)
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
               reverse('teacher:teacher-view-examinee', args=[course.id]))
    
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
    
    return render(request, 'teacher/teacher_explanation_grading.html', context)

from django.core.paginator import Paginator
@login_required(login_url='teacher:teacherlogin')
def teacher_view_department_view(request, department_id=None):
    department = get_teacher_department(request)
    student_list = SMODEL.Student.objects.filter(department=department).order_by('id')  # or 'last_name', 'first_name', etc.
    
    paginator = Paginator(student_list, 10)  # Show 10 students per page
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    context = {
        'department': department,
        'students': students,
        'student_list': student_list,
    }
    return render(request, 'teacher/teacher_view_examinee_department.html', context)
@login_required(login_url='teacher:teacherlogin')
def delete_view_student_list(request, pk):
    department = get_teacher_department(request)
    student_list = SMODEL.Student.objects.filter(id=pk,department=department)    
    student_list.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect('teacher:teacher-view-department')