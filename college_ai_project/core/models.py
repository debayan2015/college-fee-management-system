from django.db import models

class Course(models.Model):
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    admission_date = models.DateField(auto_now_add=True)
    previous_qualification = models.CharField(max_length=200, blank=True, null=True)
    marks_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    behaviour_note = models.TextField(blank=True, null=True)

    document = models.FileField(upload_to='student_documents/', blank=True, null=True)

    def total_paid(self):
        return FeePayment.objects.filter(student=self).aggregate(
            total=Sum('amount_paid')
        )['total'] or 0

    def due_amount(self):
        return self.course.total_fee - self.total_paid()

    def __str__(self):
        return self.name



class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.name} - {self.amount_paid}"
