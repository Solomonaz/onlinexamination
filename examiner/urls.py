from django.urls import path
from examiner import views
from django.contrib.auth.views import LoginView

app_name = 'examiner'

urlpatterns = [
    path('teacherlogin', LoginView.as_view(template_name='examiner/examinerlogin.html'),name='examinerlogin'),

]