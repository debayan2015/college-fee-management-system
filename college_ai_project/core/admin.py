from django.contrib import admin
from .models import Course, Student, FeePayment

admin.site.register(Course)
admin.site.register(Student)
admin.site.register(FeePayment)
