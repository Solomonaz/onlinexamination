from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from . import models
from teacher.models import Teacher
class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = models.Department
        fields = ['department_name']

class TeacherSalaryForm(forms.Form):
    salary=forms.IntegerField()

# class CourseForm(forms.ModelForm):
#     class Meta:
#         model=models.Course
#         fields=['course_name','question_number','total_marks', 'given_time', 'department']
#         widgets = {
#             'department': forms.Select(attrs={'class': 'form-control'}),
#         }

class CourseForm(forms.ModelForm):
    class Meta:
        model = models.Course
        fields = ['course_name', 'question_number', 'total_marks', 'given_time']
        
    def __init__(self, *args, **kwargs):
        # Remove department from kwargs before calling parent's __init__
        self.department = kwargs.pop('department', None)
        super().__init__(*args, **kwargs)
        
        # If department is provided, set it as initial value and hide the field
        if self.department:
            self.fields['department'] = forms.ModelChoiceField(
                queryset=models.Department.objects.filter(id=self.department.id),
                initial=self.department,
                widget=forms.HiddenInput()
            )

    def save(self, commit=True):
        # Automatically set department if it was provided
        course = super().save(commit=False)
        if self.department:
            course.department = self.department
        if commit:
            course.save()
        return course
    
class QuestionForm(forms.ModelForm):
    class Meta:
        model = models.Question
        fields = ['question_type', 'marks', 'question', 'option1', 'option2', 
                 'option3', 'option4', 'answer', 'blank_answer', 'case_sensitive']
    
    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.department = department
        
        # Add course field dynamically
        self.fields['course'] = forms.ModelChoiceField(
            queryset=models.Course.objects.filter(department=department) if department else models.Course.objects.none(),
            required=True,
            label="Course"
        )
        
        # Initialize based on question type
        question_type = self.initial.get('question_type', 'MCQ')
        if self.data:  # If form is submitted
            question_type = self.data.get('question_type', 'MCQ')
        self.set_required_fields(question_type)

    def set_required_fields(self, question_type):
        """Set required fields based on question type"""
        common_required = ['course', 'marks', 'question']
        
        if question_type == 'MCQ':
            required_fields = common_required + ['option1', 'option2','option3','option4', 'answer']
            # Hide FIB-specific fields
            self.fields['blank_answer'].required = False
            self.fields['blank_answer'].widget = forms.HiddenInput()
            self.fields['case_sensitive'].widget = forms.HiddenInput()
        else:  # FIB
            required_fields = common_required + ['blank_answer']
            # Hide MCQ-specific fields
            for option in ['option1', 'option2', 'option3', 'option4']:
                self.fields[option].required = False
                self.fields[option].widget = forms.HiddenInput()
            self.fields['answer'].required = False
            self.fields['answer'].widget = forms.HiddenInput()
        
        # Set required fields
        for field_name, field in self.fields.items():
            field.required = field_name in required_fields
        
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type', 'MCQ')
        
        # Validate course belongs to teacher's department
        course = cleaned_data.get('course')
        if course and hasattr(self, '_current_user'):
            teacher = Teacher.objects.get(user=self._current_user)
            if course.department != teacher.department:
                raise ValidationError("You can only add questions to courses in your department")
        
        # Validate question type specific fields
        if question_type == 'FIB':
            blank_answer = cleaned_data.get('blank_answer')
            if not blank_answer:
                raise forms.ValidationError("Please provide the correct answer for the blank")
            # Copy blank_answer to answer field for storage
            cleaned_data['answer'] = blank_answer
            
        return cleaned_data