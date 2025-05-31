from django.urls import path
from examiner import views
from examiner.views import ExaminerLoginView


app_name = 'examiner'

urlpatterns = [
    path('examinerclick', views.examinerclick_view),
    path('examinersignup', views.examiner_signup_view,name='examinersignup'),
    path('examinerlogin', ExaminerLoginView.as_view(), name='examinerlogin'),
    path('examiner-dashboard', views.examiner_dashboard_view,name='examiner-dashboard'),

]