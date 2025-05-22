from django.urls import path
from teacher import views
from django.contrib.auth.views import LoginView

app_name = 'teacher'

urlpatterns = [
path('teacherclick', views.teacherclick_view),
path('teacherlogin', LoginView.as_view(template_name='teacher/teacherlogin.html'),name='teacherlogin'),
path('teachersignup', views.teacher_signup_view,name='teachersignup'),
path('teacher-dashboard', views.teacher_dashboard_view,name='teacher-dashboard'),
path('teacher-exam', views.teacher_exam_view,name='teacher-exam'),
path('teacher-add-exam', views.teacher_add_exam_view,name='teacher-add-exam'),
path('teacher-view-exam', views.teacher_view_exam_view,name='teacher-view-exam'),
path('delete-exam/<int:pk>', views.delete_exam_view,name='delete-exam'),

path('teacher-view-examinee/<int:course_id>', views.teacher_view_examinees_view,name='teacher-view-examinee'),
path('teacher-view-grading/<int:student_id>/<int:course_id>/',views.teacher_explanation_grading_view, name='teacher-view-grading'),
path('teacher-view-department',views.teacher_view_department_view, name='teacher-view-department'),
path('delete-view-student-list/<int:pk>',views.delete_view_student_list, name='delete-view-student-list'),



path('teacher-question', views.teacher_question_view,name='teacher-question'),
path('teacher-add-question', views.teacher_add_question_view,name='teacher-add-question'),
path('teacher-view-question', views.teacher_view_question_view,name='teacher-view-question'),
path('see-question/<int:pk>', views.see_question_view,name='see-question'),
path('remove-question/<int:pk>', views.remove_question_view,name='remove-question'),
path('download-template/<str:type>/', views.download_question_template, name='download_template'),

path('teacher-add-question-bank', views.teacher_add_question_bank_view,name='teacher-add-question-bank'),
path('teacher-assign-question-bank', views.teacher_assign_question_bank_view,name='teacher-assign-question-bank'),

]
