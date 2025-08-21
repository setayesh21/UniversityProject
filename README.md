# UniversityProject

University Registration System

A complete university registration system implemented
with Django, including student management, courses,
enrollment, schedule conflict delection, and 
simulated payment system.

______________________________

Features  
**Student Management (registration, login/logout, profile
**Course Management (add, edit, delete by admin)  
**Course Enrollment by Student  
**Schedule Conflict Detection  
**Student Weekly Timetable  
**Payment Module (simulated: success/failure)  
**Django Admin Panel (for full management)  
**Authentication & Roles (Admin/ Student)

______________________________

Technologies
-Python 
-Django 
-Bootstrap 
-SQLite (default database)

______________________________

Getting Started

  1.Clone the Repository

  git clone http://github.com/yourusername/UniversityProject.git
  cd UniversityProject

______________________________

  2.Create and Activate Virtual Environment
   
   python -m venv venv
   source venv/bin/activate  -> On Linux/Mac
   venv\Scripts\activate  -> On Windows

______________________________

  3.Install Dependencies
   
   pip install -r requirements.txt

______________________________

  4.Apply Migrations

   python manage.py migrate

______________________________

  5.Create Superuser (Admin Panel Access)

   python manage.py createsuperuser

______________________________

  6.Run the Development Server 

   python manage.py runserver

______________________________

 Now open your browser and go to :
   
   Student Portal:
    http://127.0.0.1:8000/student/register/
   
   Admin Panel:
    http://127.0.0.1:8000/admin/

______________________________

Project Structure

 university_project
 │── manage.py  #Django management script
 │── db.sqlite3  #Defualt database
 │── registration/  #Main app (student, courses, enrollment)
   │── admin.py
   │── models.py
   │── views.py
   │── forms.py
   │── magrations/
   │── templates/ #HTML templates(Bootstrap-based)
   │── ...
 │── university_project/  #Project Setting
   │── setting.py
   │── urls.py
   │── ...
 │── venv/
 │── seed_data.py

 ______________________________

