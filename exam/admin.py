from django.contrib import admin
from . models import Question, Course, Result


admin.site.register(Question)
admin.site.register(Course)
admin.site.register(Result)

