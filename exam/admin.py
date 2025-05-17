from django.contrib import admin
from . models import Question, Course, Result, StudentAnswer, Department


admin.site.register(Course)
admin.site.register(Result)
admin.site.register(StudentAnswer)
admin.site.register(Department)



from django.contrib import admin
from .models import Question

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'question_type', 'course', 'marks')
    list_filter = ('question_type', 'course')
    fieldsets = (
        (None, {
            'fields': ('question_type', 'course', 'question', 'marks')
        }),
        ('Multiple Choice Options', {
            'fields': ('option1', 'option2', 'option3', 'option4', 'answer'),
            'classes': ('collapse',)
        }),
        ('Fill in the Blank Options', {
            'fields': ('blank_answer', 'case_sensitive'),
            'classes': ('collapse',)
        }),
    )

