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
# registration
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

#__________________________
# registration
# admin.py

from django.contrib import admin
from .models import Student, Teacher, Employee, Course, StudentCourse


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("ID", "lname", "fname", "major")
    search_fields = ("ID", "lname", "fname")

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("ID", "lname", "fname", "subject")

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("ID", "lname", "fname", "section")

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "day_of_week", "start_time", "end_time")
    list_filter = ("day_of_week",)
    search_fields = ("code", "name")

@admin.register(StudentCourse)
class StudentCourseAdmin(admin.ModelAdmin):
    list_display = ("student", "course")
    search_fields = ("student__ID", "course__code", "course__name")

#__________________________
# registration
# forms.py

from django import forms
from .models import Student, Teacher, Employee, Course

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["fname", "lname", "ID", "DoB", "major"]

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["fname", "lname", "ID", "DoB", "subject"]

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["fname", "lname", "ID", "DoB", "section"]

class StudentLookupForm(forms.Form):
    student_id = forms.CharField(label="Student ID", max_length=50)

#__________________________
# registration
# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from.models import Student, Teacher, Employee, Course, StudentCourse
from.forms import StudentForm, TeacherForm, EmployeeForm, StudentLookupForm
import logging
import json, os


logging.basicConfig(
    filename="registration.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ---- Existing basic pages (keep your previous ones) ----

def home(request):
    return render(request, "registration/home.html")

def list_people(request):
    return render(request, "registration/list.html", {
        "students": Student.objects.all(),
        "teachers": Teacher.objects.all(),
        "employees": Employee.objects.all(),
    })

# --- Student Portal: enter Student ID, then choose a course -> Checkout ---

def student_register_course(request):
    """Step 1: student enters ID, sees list of courses with Checkout buttons."""
    form = StudentLookupForm(request.POST or None)
    student = None
    student_valid = False

    if request.method == "POST" and form.is_valid():
        sid = form.cleaned_data["student_id"].strip()
        student = Student.objects.filter(ID=sid).first()
        if student:
            student_valid = True
        else:
            messages.error(request, "Student ID not found!")

    courses = Course.objects.all().order_by("day_of_week", "start_time")
    context = {
        "form": form,
        "student": student,
        "student_valid": student_valid,
        "courses": courses,
    }
    return render(request, "registration/student_register.html", context)


def _has_conflict(student: Student, new_course: Course) -> bool:
    """Check if new_course conflicts with any of student's registered courses."""
    existing = Course.objects.filter(studentcourse__student=student, day_of_week=new_course.day_of_week)
    for c in existing:
        # time overlap if start < other_end AND other_start < end
        if c.start_time < new_course.end_time and new_course.start_time < c.end_time:
            return True
    return False


def checkout_course(request, student_id: str, course_id: int):
    """Step 2: Checkout page with Success/Fail buttons."""
    student = get_object_or_404(Student, ID=student_id)
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "success":
            # Conflict check
            if _has_conflict(student, course):
                messages.error(request, "Cannot register: time conflict with an existing course.")
                logging.info(f"Checkout conflict for {student} on {course}")
            else:
                StudentCourse.objects.get_or_create(student=student, course=course)
                messages.success(request, f"Payment successful. Registered for {course.name}!")
                logging.info(f"Checkout success: {student} -> {course}")
            return redirect("my_courses", student_id=student.ID)
        elif action == "fail":
            messages.error(request, "Payment failed. Course not registered.")
            logging.info(f"Checkout failed for {student} on {course}")
            return redirect("student_register_course")

    return render(request, "registration/checkout.html", {"student": student, "course": course})


def my_courses(request, student_id: str):
    student = get_object_or_404(Student, ID=student_id)
    courses = Course.objects.filter(studentcourse__student=student).order_by("day_of_week", "start_time")
    return render(request, "registration/my_courses.html", {"student": student, "courses": courses})

# ---- (Optional) AJAX search endpoint preserved if you already had it) ----

def ajax_search(request):
    type_ = request.GET.get("type")
    keyword = request.GET.get("keyword", "").strip().lower()
    results = []

    Model = None
    if type_ == "student":
        Model = Student
    elif type_ == "teacher":
        Model = Teacher
    elif type_ == "employee":
        Model = Employee

    if Model:
        for obj in Model.objects.all():
            if keyword in str(obj).lower():
                results.append(str(obj))
    return JsonResponse({"results": results})

#__________________________
# registration
# urls.py

from django.urls import path
from.import views

urlpatterns = [
    path('', views.home, name='home'),
    path('list/', views.list_people, name='list_people'),
# Student Portal
    path('student/register/', views.student_register_course, name='student_register_course'),
    path('student/<str:student_id>/checkout/<int:course_id>/', views.checkout_course, name='checkout_course'),
    path('student/<str:student_id>/courses/', views.my_courses, name='my_courses'),

    # (optional) ajax search if used elsewhere
    path('ajax_search/', views.ajax_search, name='ajax_search'),
]

