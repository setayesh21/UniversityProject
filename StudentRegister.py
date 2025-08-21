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

#--------------------
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

#--------------------
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

#--------------------
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

#--------------------
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

#--------------------
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

#---------------------------
# registration/ templates
# base.html

<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>University Registration System</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body class="container py-4">
  <h1 class="mb-4">University Registration System</h1>
  <nav class="mb-3 d-flex gap-2 flex-wrap">
    <a class="btn btn-outline-primary btn-sm" href="{% url 'home' %}">Home</a>
    <a class="btn btn-outline-secondary btn-sm" href="{% url 'list_people' %}">People</a>
    <a class="btn btn-primary btn-sm" href="{% url 'student_register_course' %}">Student Portal</a>
  </nav>

  {% if messages %}
  <div class="my-2">
    {% for message in messages %}
      <div class="alert alert-{{ message.tags }} mb-2">{{ message }}</div>
    {% endfor %}
  </div>
  {% endif %}

  <hr>
  {% block content %}{% endblock %}
</body>
</html>

#---------------------------
# registration/ templates
# home.html

{% extends "registration/base.html" %}
{% block content %}
<p>Welcome! Use the Student Portal to enroll in courses.</p>
{% endblock %}

#---------------------------
# registration/ templates
# list.html

{% extends "registration/base.html" %}
{% block content %}
<h2>People</h2>
<h4>Students</h4>
<ul>{% for s in students %}<li>{{ s }}</li>{% empty %}<li>None</li>{% endfor %}</ul>
<h4>Teachers</h4>
<ul>{% for t in teachers %}<li>{{ t }}</li>{% empty %}<li>None</li>{% endfor %}</ul>
<h4>Employees</h4>
<ul>{% for e in employees %}<li>{{ e }}</li>{% empty %}<li>None</li>{% endfor %}</ul>
{% endblock %}

#---------------------------
# registration/ templates
# my_course.html

{% extends "registration/base.html" %}
{% block content %}
<h2>My Courses</h2>
<p><strong>{{ student.fname }} {{ student.lname }}</strong> (ID: {{ student.ID }})</p>

<ul class="list-group mb-3">
  {% for c in courses %}
    <li class="list-group-item">{{ c.code }} – {{ c.name }} ({{ c.day_of_week }} {{ c.start_time }}–{{ c.end_time }})</li>
  {% empty %}
    <li class="list-group-item">No courses registered yet.</li>
  {% endfor %}
</ul>

<a class="btn btn-primary" href="{% url 'student_register_course' %}">Register More Courses</a>
{% endblock %}

#---------------------------
# registration/ templates
# checkout.html

{% extends "registration/base.html" %}
{% block content %}
<h2>Checkout</h2>
<p><strong>Student:</strong> {{ student.fname }} {{ student.lname }} (ID: {{ student.ID }})</p>
<p><strong>Course:</strong> {{ course.name }} — {{ course.day_of_week }} {{ course.start_time }}–{{ course.end_time }}</p>

<form method="post" class="d-flex gap-2">
  {% csrf_token %}
  <button type="submit" name="action" value="success" class="btn btn-success">Payment Successful</button>
  <button type="submit" name="action" value="fail" class="btn btn-danger">Payment Failed</button>
</form>
{% endblock %}

#---------------------------
# registration/ templates
# student_register.html

{% extends "registration/base.html" %}
{% block content %}
<h2>Student Course Registration</h2>

<form method="post" class="row g-3 mb-4">
  {% csrf_token %}
  <div class="col-auto">
    {{ form.student_id.label_tag }}
    {{ form.student_id }}
  </div>
  <div class="col-auto align-self-end">
    <button type="submit" class="btn btn-success">Continue</button>
  </div>
</form>

{% if student_valid %}
  <div class="mb-3">
    <strong>Student:</strong> {{ student.fname }} {{ student.lname }} (ID: {{ student.ID }})
  </div>
  <div class="table-responsive">
    <table class="table table-striped align-middle">
      <thead>
        <tr>
          <th>Code</th><th>Name</th><th>Time</th><th></th>
        </tr>
      </thead>
      <tbody>
        {% for course in courses %}
        <tr>
          <td>{{ course.code }}</td>
          <td>{{ course.name }}</td>
          <td>{{ course.day_of_week }} {{ course.start_time }} - {{ course.end_time }}</td>
          <td>
            <a class="btn btn-primary btn-sm" href="{% url 'checkout_course' student_id=student.ID course_id=course.id %}">Checkout</a>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="4">No courses available.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
{% else %}
  <p class="text-muted">Enter your Student ID to see available courses and proceed to checkout.</p>
{% endif %}
{% endblock %}

#----------------------
# university_project
# setting.py

"""
Django settings for university_project project.

Generated by 'django-admin startproject' using Django 5.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-z+1%iqbwg91(3=d)&j%%pu0ug-2i_@os3@50v+32pzz77k%)aj'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'registration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'university_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'university_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#----------------------
# university_project
# urls.py

"""
URL configuration for university_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('registration.urls')),
]
