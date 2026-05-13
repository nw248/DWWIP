import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Course, Lesson

def test_course_creation():
    """Проверка создания курса"""
    course = Course(title='Course Title', description='Course Description')
    assert course.title == 'Course Title'
    assert course.description == 'Course Description'

def test_lesson_creation():
    """Проверка создания урока"""
    lesson = Lesson(title='Lesson 1', content='Lesson content', lesson_type='text')
    assert lesson.title == 'Lesson 1'
    assert lesson.content == 'Lesson content'
    assert lesson.lesson_type == 'text'