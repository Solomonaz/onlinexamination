from django import forms
from django.contrib.auth.models import User
from . import models

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
        
        # Add course field dynamically
        self.fields['course'] = forms.ModelChoiceField(
            queryset=models.Course.objects.filter(department=department) if department else models.Course.objects.none(),
            required=True,
            label="Course"
        )
        
        # Set required=False for all fields initially
        for field in self.fields:
            self.fields[field].required = False
            
        # Set initial question type to MCQ if new instance
        if not self.instance.pk:
            self.fields['question_type'].initial = 'MCQ'
            
        # Set required fields based on question type
        question_type = self.data.get('question_type', 'MCQ') if self.data else self.instance.question_type if self.instance.pk else 'MCQ'
        self.set_required_fields(question_type)

    def set_required_fields(self, question_type):
        """Set required fields based on question type"""
        common_required = ['course', 'marks', 'question']
        
        if question_type == 'MCQ':
            required_fields = common_required + ['option1', 'option2', 'answer']
        else:  # FIB
            required_fields = common_required + ['blank_answer']
            
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True
                
        # Hide irrelevant fields
        if question_type == 'MCQ':
            self.fields['blank_answer'].widget = forms.HiddenInput()
            self.fields['case_sensitive'].widget = forms.HiddenInput()
        else:
            for option in ['option1', 'option2', 'option3', 'option4']:
                self.fields[option].widget = forms.HiddenInput()
            self.fields['answer'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type', 'MCQ')
        from django.core.exceptions import ValidationError
        
        if hasattr(self, '_current_user'):
            teacher = models.Teacher.objects.get(user=self._current_user)
            if self.course.department != teacher.department:
                raise ValidationError("You can only add questions to courses in your department")
        
        super().clean()
        
        if question_type == 'MCQ':
            if not cleaned_data.get('option1') or not cleaned_data.get('option2'):
                raise forms.ValidationError("MCQ questions require at least two options")
                
            answer = cleaned_data.get('answer')
            if answer not in ['Option1', 'Option2', 'Option3', 'Option4']:
                raise forms.ValidationError("Please select a valid answer option")
                
        elif question_type == 'FIB':
            if not cleaned_data.get('blank_answer'):
                raise forms.ValidationError("Please provide the correct answer for the blank")
            cleaned_data['answer'] = cleaned_data['blank_answer']
            
        return cleaned_data