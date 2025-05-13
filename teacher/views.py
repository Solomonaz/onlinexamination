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
import json
from datetime import datetime
from django.http import JsonResponse
from django.db.models import Sum, Prefetch

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
            question_type = request.POST.get('question_type', 'MCQ')
            questionForm = QFORM.QuestionForm(request.POST)
            
            if questionForm.is_valid():
                question = questionForm.save(commit=False)
                course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
                question.course = course
                
                # Handle question type specific logic
                if question_type == 'FIB':
                    # For explanation questions, ensure the question_type is set to FIB
                    question.question_type = 'FIB'
                    # The form should handle the field mapping, so no need for manual field setting
                    question = questionForm.save(commit=False)
                    course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
                    question.course = course
                    question.save()
                
                question.save()
                messages.success(request, f"{question.get_question_type_display()} question added successfully!")
                return HttpResponseRedirect('/teacher/teacher-add-question')
            else:
                # Pass the form with errors back to template
                messages.error(request, "Form is invalid. Please check your inputs.")
                return render(request, 'teacher/teacher_add_question.html', {
                    'questionForm': questionForm,
                    'import_errors': request.session.pop('import_errors', None)
                })
    
    return render(request, 'teacher/teacher_add_question.html', {
        'questionForm': questionForm,
        'import_errors': request.session.pop('import_errors', None)
    })
def handle_bulk_import(request):
    try:
        course_id = request.POST.get('courseID')
        import_type = request.POST.get('import_type', 'MCQ')  # Default to MCQ
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
                if import_type == 'MCQ':
                    # Validate MCQ required fields
                    required_fields = ['question', 'marks', 'option1', 'option2', 'answer']
                    if not all(field in row for field in required_fields):
                        raise ValueError("Missing required columns for MCQ import")
                    
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
                        explanation=row.get('explanation', '')
                    )
                    
                elif import_type == 'FIB':
                    # Validate FIB required fields
                    required_fields = ['question_text', 'marks', 'blank_answer']
                    if not all(field in row for field in required_fields):
                        raise ValueError("Missing required columns for FIB import")
                    
                    QMODEL.Question.objects.create(
                        course=course,
                        question_type='FIB',
                        question=row['question_text'],
                        marks=int(row['marks']),
                        blank_answer=row['blank_answer'],
                        answer=row['blank_answer'],  # Set answer to blank_answer
                        case_sensitive=str(row.get('case_sensitive', 'false')).lower() == 'true',
                        explanation=row.get('explanation', '')
                    )
                
                success_count += 1
                
            except Exception as e:
                error_messages.append(f"Row {index+2}: {str(e)}")
        
        if success_count > 0:
            messages.success(request, f"Successfully imported {success_count} {import_type} questions!")
        if error_messages:
            messages.warning(request, f"Completed with {len(error_messages)} errors")
            request.session['import_errors'] = error_messages
        
    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
    
    return HttpResponseRedirect('/teacher/teacher-add-question')

def download_question_template(request, type):
    response = HttpResponse(content_type='text/csv')
    
    if type == 'mcq':
        response['Content-Disposition'] = 'attachment; filename="mcq_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(['question', 'marks', 'option1', 'option2', 'option3', 'option4', 'answer', 'explanation'])
        writer.writerow(['What is 2+2?', '2', '3', '4', '5', '6', 'Option2', 'Basic addition'])
    elif type == 'fib':
        response['Content-Disposition'] = 'attachment; filename="fib_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(['question_text', 'marks', 'blank_answer', 'case_sensitive', 'explanation'])
        writer.writerow(['The capital of France is _____.', '2', 'Paris', 'false', 'Paris has been capital since 508 AD'])
    
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

from django.shortcuts import get_object_or_404
@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_examinees_view(request, course_id):
    course = get_object_or_404(QMODEL.Course, id=course_id)
    results = QMODEL.Result.objects.filter(exam=course).select_related('student')
    organizations = QMODEL.Student.objects.values_list('organization', flat=True).distinct()
    
    # Initialize filter variables
    organization = request.GET.get('organization', '')
    min_mark = request.GET.get('min_mark', '')
    max_mark = request.GET.get('max_mark', '')
    exam_date = request.GET.get('exam_date', '')

    # Apply filters
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
            exam_date = ''  # Reset invalid date

    return render(request, 'teacher/teacher_view_examinee.html', {        
        'course': course,
        'results': results,
        'organizations': organizations,
        'selected_org': organization,
        'exam_date': exam_date,
        'min_mark': min_mark,
        'max_mark': max_mark,
    })

from django.http import JsonResponse
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required, user_passes_test

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Prefetch
import json

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def get_student_explanation_answers(request, course_id, student_id):
    try:
        # Convert IDs to integers
        course_id = int(course_id)
        student_id = int(student_id)
        
        # Get objects or return 404
        course = get_object_or_404(QMODEL.Course, id=course_id)
        student = get_object_or_404(QMODEL.Student, id=student_id)
        
        # Get questions and answers
        questions = QMODEL.Question.objects.filter(
            course=course,
            question_type='FIB'
        ).prefetch_related(
            Prefetch('studentanswer_set',
                   queryset=QMODEL.StudentAnswer.objects.filter(student=student),
                   to_attr='student_answer'
            )
        )
        
        questions_data = []
        for question in questions:
            answer_data = {
                'id': question.id,
                'question_text': question.question,
                'max_marks': question.marks,
                'student_answer': "No answer provided",
                'graded_marks': 0
            }
            
            # Check if student answered this question
            if hasattr(question, 'student_answer') and question.student_answer:
                answer = question.student_answer[0]
                answer_data['student_answer'] = answer.answer or "No answer provided"
                answer_data['graded_marks'] = answer.marks_obtained if answer.marks_obtained is not None else 0
            
            questions_data.append(answer_data)
        
        return JsonResponse({
            'success': True,
            'student_name': student.get_name(),
            'course_name': course.course_name,
            'questions': questions_data
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f"Invalid ID format: {str(e)}"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
import json
from django.db.models import Sum

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def save_explanation_grades(request, course_id, student_id):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                }, status=400)
            
            student = QMODEL.Student.objects.get(id=student_id)
            course = QMODEL.Course.objects.get(id=course_id)
            
            # Save each graded question
            for graded_question in data.get('grades', []):
                question = QMODEL.Question.objects.get(id=graded_question['question_id'])
                
                # Update or create the StudentAnswer record
                student_answer, created = QMODEL.StudentAnswer.objects.update_or_create(
                    student=student,
                    question=question,
                    defaults={
                        'marks_obtained': graded_question['marks'],
                        'feedback': graded_question['feedback'],
                        'is_graded': True
                    }
                )
            
            # Update the total marks in the Result table
            total_marks = QMODEL.StudentAnswer.objects.filter(
                student=student,
                question__course=course,
                is_graded=True
            ).aggregate(total_marks=Sum('marks_obtained'))['total_marks'] or 0
            
            # Update the result record
            result = QMODEL.Result.objects.get(student=student, exam=course)
            result.marks = total_marks
            result.save()
            
            return JsonResponse({'success': True})
            
        except QMODEL.Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student not found'
            }, status=404)
        except QMODEL.Course.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Course not found'
            }, status=404)
        except QMODEL.Question.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Question not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)