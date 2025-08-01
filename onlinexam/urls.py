from django.urls import path,include
from django.contrib import admin
from exam import views
from django.contrib.auth.views import LogoutView,LoginView
urlpatterns = [
   
    path('grappelli/', include('grappelli.urls')),
    path('admin_panel/', admin.site.urls),
    path('teacher/',include('teacher.urls', namespace='teacher')),
    path('student/',include('student.urls')),
    path('examiner/', include('examiner.urls', namespace='examiner')),
    


    path('',views.frontpage,name=''),
    path('add-student/',views.home_view,name=''),
    path('logout', views.admin_logout_view,name='logout'),
    path('contactus', views.contactus_view),
    path('afterlogin', views.afterlogin_view,name='afterlogin'),



    path('adminclick', views.adminclick_view),
    path('adminlogin', LoginView.as_view(template_name='exam/adminlogin.html'),name='adminlogin'),
    path('admin-dashboard', views.admin_dashboard_view,name='admin-dashboard'),

    path('admin-department', views.admin_department_view,name='admin-department'),
    path('admin-add-department', views.admin_add_department_view,name='admin-add-department'),
    path('delete-department/<int:pk>', views.delete_department,name='delete-department'),

    path('admin-teacher', views.admin_teacher_view,name='admin-teacher'),
    path('admin-view-teacher', views.admin_view_teacher_view,name='admin-view-teacher'),
    path('update-teacher/<int:pk>', views.update_teacher_view,name='update-teacher'),
    path('delete-teacher/<int:pk>', views.delete_teacher_view,name='delete-teacher'),

    path('admin-student', views.admin_student_view,name='admin-student'),
    path('admin-view-student', views.admin_view_student_view,name='admin-view-student'),
    path('admin-view-student-marks', views.admin_view_student_marks_view,name='admin-view-student-marks'),
    path('admin-view-marks/<int:pk>', views.admin_view_marks_view,name='admin-view-marks'),
    path('admin-check-marks/<int:pk>', views.admin_check_marks_view,name='admin-check-marks'),
    path('update-student/<int:pk>', views.update_student_view,name='update-student'),
    path('delete-student/<int:pk>', views.delete_student_view,name='delete-student'),


    path('admin-view-examinees/<int:course_id>/', views.admin_view_examinees_view, name='admin-view-examinees'),
    path('admin-report', views.report_view, name = 'report-view'),
    path('delete-log/<int:pk>/', views.delete_log_entry, name='delete-log'),
    path('print-logs/', views.print_logs_view, name='print-logs'),


    path('admin-course', views.admin_course_view,name='admin-course'),
    path('admin-add-course', views.admin_add_course_view,name='admin-add-course'),
    path('admin-view-course', views.admin_view_course_view,name='admin-view-course'),
    path('delete-course/<int:pk>', views.delete_course_view,name='delete-course'),

    path('admin-question', views.admin_question_view,name='admin-question'),
    path('admin-add-question', views.admin_add_question_view,name='admin-add-question'),
    path('admin-view-question', views.admin_view_question_view,name='admin-view-question'),
    path('view-question/<int:pk>', views.view_question_view,name='view-question'),
    path('delete-question/<int:pk>', views.delete_question_view,name='delete-question'),

    path('logs/bulk-delete/', views.bulk_delete_logs, name='bulk-delete-logs'),

]

