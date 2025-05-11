from django import forms
from django.contrib.auth.models import User
from . import models

class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

class TeacherSalaryForm(forms.Form):
    salary=forms.IntegerField()

class CourseForm(forms.ModelForm):
    class Meta:
        model=models.Course
        fields=['course_name','question_number','total_marks', 'given_time']

# class QuestionForm(forms.ModelForm):
#     courseID=forms.ModelChoiceField(queryset=models.Course.objects.all(),empty_label="Course Name", to_field_name="id")
#     class Meta:
#         model=models.Question
#         fields=['marks','question','option1','option2','option3','option4','answer']
#         widgets = {
#             'question': forms.Textarea(attrs={'rows': 3, 'cols': 50})
#         }

class QuestionForm(forms.ModelForm):
    # Course selection field (unchanged)
    courseID = forms.ModelChoiceField(
        queryset=models.Course.objects.all(),
        empty_label="Course Name",
        to_field_name="id",
        label="Course"
    )
    
    class Meta:
        model = models.Question
        fields = ['question_type', 'marks', 'question', 'option1', 'option2', 
                 'option3', 'option4', 'answer', 'blank_answer', 'case_sensitive', 'explanation']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'cols': 50}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'cols': 50}),
            'question_type': forms.Select(attrs={'id': 'questionTypeSelect'}),
            'blank_answer': forms.TextInput(attrs={'placeholder': 'Enter the correct answer'}),
        }
        labels = {
            'question': 'Question Text',
            'blank_answer': 'Correct Answer',
        }
        help_texts = {
            'case_sensitive': 'Check this if the answer should be case sensitive',
            'explanation': 'Explanation for the correct answer (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set required=False for all fields initially
        for field in self.fields:
            self.fields[field].required = False
            
        # Set initial question type to MCQ if new instance
        if not self.instance.pk:
            self.fields['question_type'].initial = 'MCQ'
            
        # Set required fields based on question type
        if 'question_type' in self.data:  # Form was submitted
            question_type = self.data.get('question_type', 'MCQ')
        elif self.instance.pk:  # Existing instance
            question_type = self.instance.question_type
        else:  # New instance
            question_type = 'MCQ'
        
        self.set_required_fields(question_type)

    def set_required_fields(self, question_type):
        """Set required fields based on question type"""
        common_required = ['courseID', 'marks', 'question']
        
        if question_type == 'MCQ':
            required_fields = common_required + ['option1', 'option2', 'answer']
            self.fields['answer'].choices = self.instance.cat  # Use the existing choices
        else:  # FIB
            required_fields = common_required + ['blank_answer']
            self.fields['answer'].required = False  # Will be set from blank_answer
            
        # Set required attributes
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
        
        if question_type == 'MCQ':
            # Validate that at least options 1 and 2 are provided
            if not cleaned_data.get('option1') or not cleaned_data.get('option2'):
                raise forms.ValidationError("MCQ questions require at least two options")
                
            # Validate answer is one of the options
            answer = cleaned_data.get('answer')
            if answer not in ['Option1', 'Option2', 'Option3', 'Option4']:
                raise forms.ValidationError("Please select a valid answer option")
                
        elif question_type == 'FIB':
            # Validate blank answer exists
            if not cleaned_data.get('blank_answer'):
                raise forms.ValidationError("Please provide the correct answer for the blank")
            
            # Set the answer field to the blank answer
            cleaned_data['answer'] = cleaned_data['blank_answer']
            
        return cleaned_data

    def save(self, commit=True):
        question = super().save(commit=False)
        question.course = self.cleaned_data['courseID']
        
        if commit:
            question.save()
        return question