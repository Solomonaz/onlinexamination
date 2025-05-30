from django.urls import path
from examiner import views
from django.contrib.auth.views import LoginView

app_name = 'examiner'

urlpatterns = [
    path('examinersignup', views.examiner_signup_view,name='examinersignup'),
    path('examinerlogin', LoginView.as_view(template_name='examiner/examinerlogin.html'),name='examinerlogin'),

]