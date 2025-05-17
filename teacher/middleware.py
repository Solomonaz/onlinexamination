from django.shortcuts import redirect
from django.urls import reverse

class TeacherAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.groups.filter(name='TEACHER').exists():
            teacher = request.user.teacher
            if not teacher:
                return redirect('teacher_login')
            
            # Store department in request for easy access
            request.teacher_department = teacher.department