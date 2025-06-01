from django.urls import path
from examiner import views
from examiner.views import ExaminerLoginView


app_name = 'examiner'

urlpatterns = [
    path('examinerclick', views.examinerclick_view),
    path('examinersignup', views.examiner_signup_view,name='examinersignup'),
    path('examinerlogin', ExaminerLoginView.as_view(), name='examinerlogin'),
    path('examiner-dashboard', views.examiner_dashboard_view,name='examiner-dashboard'),
    path('examiner-assigned-exam', views.examiner_assinged_exam_view,name='examiner-assigned-exam'),

    path('examiner-view-examinee/<int:course_id>', views.examiner_view_examinees_view,name='examiner-view-examinee'),
    path('examiner-view-grading/<int:student_id>/<int:course_id>/',views.examiner_explanation_grading_view, name='examiner-view-grading'),
    # path('examiner-view-grading',views.examiner_explanation_grading_view, name='examiner-view-grading'),

    ]