#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

#__________________________
# Base Classes
# models.py

from django.db import models

class Person(models.Model):
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    ID = models.CharField(max_length=50, unique=True, primary_key=True)
    DoB = models.DateField()

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.lname}, {self.fname} (ID: {self.ID})"

class Student(Person):
    major = models.CharField(max_length=100)

class Teacher(Person):
    subject = models.CharField(max_length=100)

class Employee(Person):
    section = models.CharField(max_length=100)

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Added for conflict detection
    day_of_week = models.CharField(
        max_length=10,
        choices=[
            ("Mon", "Monday"), ("Tue", "Tuesday"), ("Wed", "Wednesday"),
            ("Thu", "Thursday"), ("Fri", "Friday"), ("Sat", "Saturday"), ("Sun", "Sunday"),
        ],
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.code} - {self.name} ({self.day_of_week} {self.start_time}-{self.end_time})"

class StudentCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("student", "course")  # prevent duplicate enrollments

    def __str__(self):
        return f"{self.student} -> {self.course}"

