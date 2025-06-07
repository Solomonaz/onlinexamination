from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Q
from django.core.mail import send_mail
from teacher import models as TMODEL
from examiner import models as EMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.core.paginator import Paginator
from .utils import log_activity
from django.contrib.contenttypes.models import ContentType
from .models import SystemLog
from django.utils.timesince import timesince
from django.utils import timezone
from django.contrib.admin.models import LogEntry, CHANGE
from django.utils.timezone import now

def frontpage(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'exam/frontpage.html')

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'exam/index.html')


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

def is_examiner(user):
    return user.groups.filter(name='EXAMINER').exists()

def afterlogin_view(request):
    try:
        if is_examiner(request.user):
            return redirect('examiner:examiner-dashboard')
        elif is_teacher(request.user):
            return redirect('teacher:teacher-dashboard')
        elif is_student(request.user):
            return redirect('student-dashboard')
        else:
            return redirect('admin-dashboard')
    except AttributeError: 
        if request.user.is_superuser:
            return redirect('admin-dashboard')
        return redirect('logout') 

def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')

def get_active_students():
    sessions = Session.objects.filter(expire_date__gte=now())
    uid_list = []
    for session in sessions:
        try:
            data = session.get_decoded()
            uid = data.get('_auth_user_id')
            if uid:
                uid_list.append(uid)
        except Exception:
            continue

    student_users = User.objects.filter(id__in=uid_list, groups__name='STUDENT')
    return SMODEL.Student.objects.filter(user__in=student_users)

@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    active_students = get_active_students()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        students_data = [{
            "name": student.user.get_full_name(),
            "username": student.user.username,
            "course": student.course.course_name,
            "organization": student.organization,
        } for student in active_students]
        return JsonResponse({'active_students': students_data})
    
    # Get all logs with pagination
    all_logs = SystemLog.objects.select_related('user', 'content_type').order_by('-action_time')
    paginator = Paginator(all_logs, 5)  # Show 10 logs per page
    page_number = request.GET.get('page')
    recent_logs = paginator.get_page(page_number)
    
    # Format logs for display
    now = timezone.now()
    for log in recent_logs:
        log.time_ago = timesince(log.action_time, now) + " ago"
        log.get_action_type_display = dict(SystemLog.ACTION_CHOICES).get(log.action_type, 'Other')
    
    context = {
        'total_student': SMODEL.Student.objects.all().count(),
        'team_leader_count': TMODEL.Teacher.objects.all().count(),
        'examiner_count': EMODEL.Examiner.objects.all().count(),
        'total_staff': EMODEL.Examiner.objects.all().count() + TMODEL.Teacher.objects.all().count(),
        'total_course': models.Course.objects.all().count(),
        'total_question': models.Question.objects.all().count(),
        'active_students': active_students, 
        'recent_logs': recent_logs,
        'paginator': paginator,
        'page_obj': recent_logs,
    }
    return render(request,'exam/admin_dashboard.html', context)

@login_required(login_url='adminlogin')
def print_logs_view(request):
    """View to handle printing of activity logs"""
    logs = SystemLog.objects.select_related('user', 'content_type').order_by('-action_time')
    now = timezone.now()
    
    for log in logs:
        log.time_ago = timesince(log.action_time, now) + " ago"
        log.get_action_type_display = dict(SystemLog.ACTION_CHOICES).get(log.action_type, 'Other')
    
    return render(request, 'exam/print_logs.html', {
        'logs': logs,
        'print_date': timezone.now(),
    })

@login_required(login_url='adminlogin')
# @user_passes_test(lambda u: u.is_superuser)
def delete_log_entry(request, pk):
    if request.method == 'POST':
        SystemLog.objects.filter(pk=pk).delete()
    return HttpResponseRedirect(reverse('admin-dashboard'))

@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    dict={
    'total_teacher':TMODEL.Teacher.objects.all().count(),
    }
    return render(request,'exam/admin_teacher.html',context=dict)

from itertools import chain
@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all()
    examiners= EMODEL.Examiner.objects.all()
    combined_staff = list(chain(teachers, examiners))
    
    context = {
        'staff': combined_staff,
    }
    return render(request,'exam/admin_view_teacher.html',context)


@login_required(login_url='adminlogin')
def update_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=TMODEL.User.objects.get(id=teacher.user_id)
    userForm=TFORM.TeacherUserForm(instance=user)
    teacherForm=TFORM.TeacherForm(request.FILES,instance=teacher)
    mydict={'userForm':userForm,'teacherForm':teacherForm}
    if request.method=='POST':
        userForm=TFORM.TeacherUserForm(request.POST,instance=user)
        teacherForm=TFORM.TeacherForm(request.POST,request.FILES,instance=teacher)
        if userForm.is_valid() and teacherForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            teacherForm.save()
            return redirect('admin-view-teacher')
    return render(request,'exam/update_teacher.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_teacher_view(request,pk):
    teacher=EMODEL.Examiner.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-teacher')


@login_required(login_url='adminlogin')
def admin_view_teacher_salary_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=True)
    return render(request,'exam/admin_view_teacher_salary.html',{'teachers':teachers})




@login_required(login_url='adminlogin')
def admin_student_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    }
    return render(request,'exam/admin_student.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    student_list = SMODEL.Student.objects.all().order_by('id')
    paginator = Paginator(student_list, 10)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    return render(request, 'exam/admin_view_student.html', {'students': students})



@login_required(login_url='adminlogin')
def update_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=SMODEL.User.objects.get(id=student.user_id)
    userForm=SFORM.StudentUserForm(instance=user)
    studentForm=SFORM.StudentForm(request.FILES,instance=student)
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=SFORM.StudentUserForm(request.POST,instance=user)
        studentForm=SFORM.StudentForm(request.POST,request.FILES,instance=student)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            studentForm.save()
            return redirect('admin-view-student')
    return render(request,'exam/update_student.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return HttpResponseRedirect('/admin-view-student')


@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request,'exam/admin_course.html')


@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm=forms.CourseForm()
    if request.method=='POST':
        courseForm=forms.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-course')
    return render(request,'exam/admin_add_course.html',{'courseForm':courseForm})

from django.db.models import Count
@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.annotate(examinee_count=Count('result'))
    return render(request,'exam/admin_view_course.html',{'courses':courses})

@login_required(login_url='adminlogin')
def admin_view_examinees_view(request, course_id):
    course = models.Course.objects.get(id=course_id)
    results = models.Result.objects.filter(exam=course).select_related('student')

    return render(request, 'exam/admin_view_examinees.html', {
        'course': course,
        'results': results
    })

@login_required(login_url='adminlogin')
def delete_course_view(request,pk):
    course=models.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/admin-view-course')



@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request,'exam/admin_question.html')


@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm = forms.QuestionForm()
    if request.method == 'POST':
        questionForm = forms.QuestionForm(request.POST)
        if questionForm.is_valid():
            try:
                question = questionForm.save(commit=False)
                course = models.Course.objects.get(id=request.POST.get('courseID'))
                question.course = course
                question.save()
                messages.success(request, "Question added successfully!")
            except Exception as e:
                messages.error(request, f"An error occurred while adding the question: {str(e)}")
        else:
            messages.error(request, "Form is invalid. Please correct the errors and try again.")
        
        return HttpResponseRedirect('/admin-add-question')
    
    return render(request, 'exam/admin_add_question.html', {'questionForm': questionForm})


@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses= models.Course.objects.all()
    return render(request,'exam/admin_view_question.html',{'courses':courses})

@login_required(login_url='adminlogin')
def view_question_view(request,pk):
    questions=models.Question.objects.all().filter(course_id=pk)
    return render(request,'exam/view_question.html',{'questions':questions})

@login_required(login_url='adminlogin')
def delete_question_view(request,pk):
    question=models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')

@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students = SMODEL.Student.objects.all().order_by('user')
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)

    context = {
        'students': students_page,
    }
    return render(request, 'exam/admin_view_student_marks.html', context)

@login_required(login_url='adminlogin')
def admin_view_marks_view(request, pk):
    # Filter courses the student has a result for
    courses = models.Course.objects.filter(result__student__id=pk).distinct()

    response = render(request, 'exam/admin_view_marks.html', {'courses': courses})
    response.set_cookie('student_id', str(pk))
    return response

@login_required(login_url='adminlogin')
def admin_check_marks_view(request,pk):
    course = models.Course.objects.get(id=pk)
    student_id = request.COOKIES.get('student_id')
    student= SMODEL.Student.objects.get(id=student_id)

    results= models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'exam/admin_check_marks.html',{'results':results})
    

def aboutus_view(request):
    return render(request,'exam/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'exam/contactussuccess.html')
    return render(request, 'exam/contactus.html', {'form':sub})

from datetime import datetime
from django.db.models import Sum
@login_required(login_url='adminlogin')
def report_view(request):
    # Get all distinct courses and organizations
    courses = models.Course.objects.all()
    organizations = models.Student.objects.values_list('organization', flat=True).distinct()

    # Start with base queryset
    results = models.Result.objects.select_related('student', 'exam').order_by('-date')

    # Get filter parameters from request
    course_id = request.GET.get('course')
    organization = request.GET.get('organization')
    min_mark = request.GET.get('min_mark')
    max_mark = request.GET.get('max_mark')
    exam_date = request.GET.get('exam_date')

    # Apply filters
    if course_id:
        results = results.filter(exam__id=course_id)
    if organization:
        results = results.filter(student__organization=organization)
    if exam_date:
        try:
            date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            results = results.filter(date__date=date_obj)
        except ValueError:
            pass 

    # Get student IDs after filtering
    student_ids = [result.student.id for result in results]

    # Calculate FIB scores only for filtered students
    fib_answers = models.StudentAnswer.objects.filter(
        student_id__in=student_ids,
        question__question_type='FIB'
    ).values('student').annotate(fib_score=Sum('marks_obtained'))

    fib_scores = {answer['student']: answer['fib_score'] or 0 for answer in fib_answers}

    # Apply score range filter after calculating total scores
    filtered_results = []
    for result in results:
        result.fib_score = fib_scores.get(result.student.id, 0)
        result.total_score = result.marks + result.fib_score
        
        # Apply score range filtering manually since we need to check total_score
        if min_mark and result.total_score < int(min_mark):
            continue
        if max_mark and result.total_score > int(max_mark):
            continue
        filtered_results.append(result)

    # Convert to a list for pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(filtered_results, 10)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'results': page_obj,
        'courses': courses,
        'organizations': organizations,
        'selected_course': course_id,
        'selected_org': organization,
        'min_mark': min_mark,
        'max_mark': max_mark,
        'selected_date': exam_date,
    }
    return render(request, 'exam/report_view.html', context)

@login_required(login_url='adminlogin')
def admin_department_view(request):
    departments = models.Department.objects.all()
    context = {
        'departments':departments
    }
    return render(request, 'exam/department.html', context)



@login_required(login_url='adminlogin')
def admin_add_department_view(request):
    departmentForm = forms.DepartmentForm()
    if request.method == 'POST':
        departmentForm = forms.DepartmentForm(request.POST)
        if departmentForm.is_valid():        
            department = departmentForm.save()
    
            # Log the creation
            log_activity(
                user=request.user,
                action_type='CREATE',
                content_object=department,
                description=f'New department {department.department_name} created'
            )
            
            messages.success(request, "Department added successfully!")
            return HttpResponseRedirect('/admin-add-department')
        else:
            messages.error(request, "Please correct the errors below.")
    return render(request, 'exam/admin_add_department.html', {'departmentForm': departmentForm})

@login_required(login_url='adminlogin')
def delete_department(request, pk):
    department = models.Department.objects.get(id=pk)
    
    # Log the deletion
    log_activity(
        user=request.user,
        action_type='DELETE',
        content_object=department,
        description=f'Department {department.department_name} deleted from system'
    )
    
    department.delete()
    return HttpResponseRedirect('/admin-department')
