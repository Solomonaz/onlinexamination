from django.db import models
from student.models import Student


class Course(models.Model):
   course_name = models.CharField(max_length=50)
   question_number = models.PositiveIntegerField()
   total_marks = models.PositiveIntegerField()
   given_time = models.PositiveIntegerField(default=60)

   def __str__(self):
        return self.course_name

# class Question(models.Model):
#     course=models.ForeignKey(Course,on_delete=models.CASCADE)
#     marks=models.PositiveIntegerField()
#     question=models.CharField(max_length=600)
#     option1=models.CharField(max_length=200)
#     option2=models.CharField(max_length=200)
#     option3=models.CharField(max_length=200)
#     option4=models.CharField(max_length=200)
#     cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
#     answer=models.CharField(max_length=200,choices=cat)

class Question(models.Model):
    # Question Types
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice Question'),
        ('FIB', 'Fill in the Blank'),
    )
    
    # Common Fields for All Question Types
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES, default='MCQ',verbose_name="Question Type")
    question = models.CharField(max_length=600)
    marks = models.PositiveIntegerField()
    explanation = models.TextField(blank=True, null=True,verbose_name="Explanation",help_text="Explanation for the correct answer")
    
    # Link to parent question for explanation questions
    related_question = models.ForeignKey('self', on_delete=models.SET_NULL, 
                                       blank=True, null=True,
                                       verbose_name="Related Question",
                                       help_text="For explanation questions, link to the main question",
                                       related_name='explanations')
    
    # Fields Specific to Multiple Choice Questions
    option1 = models.CharField(max_length=200, blank=True, null=True,verbose_name="Option 1")
    option2 = models.CharField(max_length=200, blank=True, null=True,verbose_name="Option 2")
    option3 = models.CharField(max_length=200, blank=True, null=True,verbose_name="Option 3")
    option4 = models.CharField(max_length=200, blank=True, null=True,verbose_name="Option 4")
    cat = (('Option1', 'Option1'),('Option2', 'Option2'),('Option3', 'Option3'),('Option4', 'Option4'))
    
    # Answer Field (Handles both MCQ and FIB)
    answer = models.CharField(max_length=200, blank=True, null=True,verbose_name="Correct Answer", choices=cat)
    
    # For Fill-in-the-Blank Questions
    blank_answer = models.CharField(max_length=200, blank=True, null=True,verbose_name="Blank Answer",help_text="Correct answer for explanation questions")
    case_sensitive = models.BooleanField(default=False,verbose_name="Case Sensitive",help_text="Should the answer be case sensitive?") 
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['course', 'question_type']
    
    def __str__(self):
        return f"{self.question[:50]}... ({self.get_question_type_display()})"
    
    def clean(self):
        """Validate based on question type"""
        from django.core.exceptions import ValidationError
        
        if self.question_type == 'MCQ':
            # Validate MCQ fields - match form validation
            if not all([self.option1, self.option2, self.answer]):
                raise ValidationError("MCQ questions require at least two options and an answer")
            if self.answer not in ['Option1', 'Option2', 'Option3', 'Option4']:
                raise ValidationError("Invalid answer choice for MCQ")
            
            # Clear FIB-specific fields
            self.blank_answer = None
            self.case_sensitive = False
            
        elif self.question_type == 'FIB':
            # Validate FIB fields
            if not self.blank_answer:
                raise ValidationError("Explanation questions require a blank answer")
            
            # Set the answer field to the blank answer
            self.answer = self.blank_answer
            
            # Clear MCQ-specific fields
            self.option1 = None
            self.option2 = None
            self.option3 = None
            self.option4 = None
    
    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving
        super().save(*args, **kwargs)

class Result(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    exam = models.ForeignKey(Course,on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)

class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    marks_obtained = models.PositiveIntegerField(default=0)
    feedback = models.TextField(blank=True, null=True)
    is_graded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'question')
        verbose_name = "Student Answer"
        verbose_name_plural = "Student Answers"

    def __str__(self):
        return f"{self.student.user.username} - {self.question.question[:50]}..."