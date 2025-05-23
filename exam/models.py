from django.db import models
from student.models import Student
from django.apps import apps



class Department(models.Model):
   department_name = models.CharField(max_length=100, unique=True)
   
   def __str__(self):
        return self.department_name

from django.core.exceptions import ValidationError
class Course(models.Model):
    course_name = models.CharField(max_length=50)
    question_number = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField(default=100)
    given_time = models.PositiveIntegerField(default=60)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='course_set')

    def __str__(self):
        return self.course_name

    def get_random_questions(self):
        """Get random questions ensuring total marks = 100"""
        all_questions = list(self.questions.all())
        if not all_questions:
            return []
            
        total_possible = sum(q.marks for q in all_questions)
        if total_possible == 0:
            return []
            
        selected_questions = []
        remaining_marks = 100
        
        # Try to find combination that sums to exactly 100
        for attempt in range(100):
            temp_questions = []
            temp_total = 0
            for q in all_questions:
                if temp_total + q.marks <= 100:
                    temp_questions.append(q)
                    temp_total += q.marks
                    if temp_total == 100:
                        return temp_questions
            
        # If no exact combination, adjust marks proportionally
        for q in all_questions:
            adjusted_mark = round((q.marks / total_possible) * 100)
            q.marks = adjusted_mark
            selected_questions.append(q)
            
        return selected_questions

class QuestionBank(models.Model):
    """model to represent question banks"""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)
    courses = models.ManyToManyField(Course, related_name='question_banks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def clean(self):
        # Ensure only one bank can be active at a time
        if self.is_active:
            active_banks = QuestionBank.objects.filter(is_active=True)
            if active_banks.exists() and active_banks.first() != self:
                raise ValidationError("Only one question bank can be active at a time")

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other banks when saving this one as active
            QuestionBank.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Question(models.Model):
    # Common Fields for All Question Types
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice Question'),
        ('FIB', 'Fill in the Blank'),
    )
    
    # Changed related_name from default 'question_set' to 'questions'
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES, default='MCQ', verbose_name="Question Type")
    question = models.CharField(max_length=600)
    marks = models.PositiveIntegerField()

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


class ActiveQuestion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='active_questions')
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('course', 'question')