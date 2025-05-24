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
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.http import JsonResponse
from django.core.paginator import Paginator

from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.utils.timesince import timesince
from django.utils.timezone import now
from django.contrib.admin.models import LogEntry, CHANGE

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

# def afterlogin_view(request):
#     if is_student(request.user):      
#         return redirect('student/student-dashboard')
                
#     elif is_teacher(request.user):
#         accountapproval=TMODEL.Teacher.objects.all().filter(user_id=request.user.id,status=True)
#         if accountapproval:
#             return redirect('teacher/teacher-dashboard')
#         else:
#             return render(request,'teacher/teacher_wait_for_approval.html')
#     else:
#         return redirect('admin-dashboard')

def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')
                
    elif is_teacher(request.user):
        return redirect('teacher/teacher-dashboard')
    else:
        return redirect('admin-dashboard')

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
        
    recent_logs = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:5]
    for log in recent_logs:
        log.time_ago = timesince(log.action_time, now()) + " ago"

    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    'total_teacher':TMODEL.Teacher.objects.all().filter(status=True).count(),
    'total_course':models.Course.objects.all().count(),
    'total_question':models.Question.objects.all().count(),
    'active_students': active_students, 
    'recent_logs':recent_logs,
    }
    return render(request,'exam/admin_dashboard.html',context=dict)

@login_required(login_url='adminlogin')
# @user_passes_test(lambda u: u.is_superuser)
def delete_log_entry(request, pk):
    if request.method == 'POST':
        LogEntry.objects.filter(pk=pk).delete()
    return HttpResponseRedirect(reverse('admin-dashboard'))

@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    dict={
    'total_teacher':TMODEL.Teacher.objects.all().count(),
    }
    return render(request,'exam/admin_teacher.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all()
    return render(request,'exam/admin_view_teacher.html',{'teachers':teachers})


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
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-teacher')




# @login_required(login_url='adminlogin')
# def admin_view_pending_teacher_view(request):
#     teachers= TMODEL.Teacher.objects.all().filter(status=False)
#     return render(request,'exam/admin_view_pending_teacher.html',{'teachers':teachers})


# @login_required(login_url='adminlogin')
# def approve_teacher_view(request,pk):
#     teacherSalary=forms.TeacherSalaryForm()
#     if request.method=='POST':
#         teacherSalary=forms.TeacherSalaryForm(request.POST)
#         if teacherSalary.is_valid():
#             teacher=TMODEL.Teacher.objects.get(id=pk)
#             teacher.salary=teacherSalary.cleaned_data['salary']
#             teacher.status=True
#             teacher.save()
#         else:
#             print("form is invalid")
#         return HttpResponseRedirect('/admin-view-pending-teacher')
#     return render(request,'exam/salary_form.html',{'teacherSalary':teacherSalary})

# @login_required(login_url='adminlogin')
# def reject_teacher_view(request,pk):
#     teacher=TMODEL.Teacher.objects.get(id=pk)
#     user=User.objects.get(id=teacher.user_id)
#     user.delete()
#     teacher.delete()
#     return HttpResponseRedirect('/admin-view-pending-teacher')

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
    students= SMODEL.Student.objects.all()
    return render(request,'exam/admin_view_student_marks.html',{'students':students})

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


from django.db.models import Q
from exam import models 
@login_required(login_url='adminlogin')
def report_view(request):
    courses = models.Course.objects.all()
    organizations = models.Student.objects.values_list('organization', flat=True).distinct()

    results = models.Result.objects.select_related('student', 'exam')

    course_id = request.GET.get('course')
    organization = request.GET.get('organization')
    min_mark = request.GET.get('min_mark')
    max_mark = request.GET.get('max_mark')

    if course_id:
        results = results.filter(exam__id=course_id)
    if organization:
        results = results.filter(student__organization=organization)
    if min_mark:
        results = results.filter(marks__gte=min_mark)
    if max_mark:
        results = results.filter(marks__lte=max_mark)

    context = {
        'results': results,
        'courses': courses,
        'organizations': organizations,
        'selected_course': course_id,
        'selected_org': organization,
        'min_mark': min_mark,
        'max_mark': max_mark,
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
            departmentForm.save()
            messages.success(request, "Department added successfully!")
            return HttpResponseRedirect('/admin-add-department')
        else:
            messages.error(request, "Please correct the errors below.")
    return render(request, 'exam/admin_add_department.html', {'departmentForm': departmentForm})