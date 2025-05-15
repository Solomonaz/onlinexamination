from django.core.management.base import BaseCommand
from exam.models import Course, ActiveQuestion, Question
import random

class Command(BaseCommand):
    help = 'Set active questions for all courses to ensure 100 total marks'

    def handle(self, *args, **options):
        for course in Course.objects.all():
            # Clear existing active questions
            course.active_questions.all().delete()
            
            # Get all questions for this course
            all_questions = list(course.questions.all())
            
            # Select questions until we reach ~100 marks
            selected_questions = []
            total_marks = 0
            random.shuffle(all_questions)
            
            for question in all_questions:
                if total_marks + question.marks <= 100:
                    ActiveQuestion.objects.create(
                        course=course,
                        question=question,
                        is_active=True
                    )
                    total_marks += question.marks
                    selected_questions.append(question)
                    if total_marks >= 100:
                        break
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Set {len(selected_questions)} questions ({total_marks} marks) '
                    f'for course: {course.course_name}'
                )
            )