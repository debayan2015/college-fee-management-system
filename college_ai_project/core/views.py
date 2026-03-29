from django.shortcuts import render
from .models import Student, Course, FeePayment
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
import json
import calendar
import openai

openai.api_key = "YOUR_API_KEY_HERE"

from django.http import JsonResponse
from django.db.models import Sum
from .models import Student, FeePayment

def chatbot_api(request):
    msg = request.GET.get('msg', '')

  
    students = Student.objects.all()
    data = []

    for s in students:
        paid = FeePayment.objects.filter(student=s).aggregate(
            Sum('amount_paid')
        )['amount_paid__sum'] or 0

        due = s.course.total_fee - paid

        data.append({
            "name": s.name,
            "course": s.course.name,
            "due": float(due)
        })

   
    prompt = f"""
    You are an AI assistant for a college management system.

    Here is student data:
    {data}

    Answer this question:
    {msg}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        reply = response['choices'][0]['message']['content']

    except Exception as e:
        reply = "AI error: " + str(e)

    return JsonResponse({'reply': reply})

def dashboard(request):
    total_students = Student.objects.count()
    total_courses = Course.objects.count()

    total_revenue = FeePayment.objects.aggregate(
        Sum('amount_paid')
    )['amount_paid__sum'] or 0

    students = Student.objects.all()

    total_due = 0
    due_students = []
    students_data = []

    for student in students:
        total_fee = student.course.total_fee

        paid = FeePayment.objects.filter(student=student).aggregate(
            Sum('amount_paid')
        )['amount_paid__sum'] or 0

        due = total_fee - paid
        total_due += due

        # Due list
        if due > 0:
            due_students.append({
            'student_id': student.id,   
            'name': student.name,
            'course': student.course.name,
            'due': due
        })

        # Student overview
        risk = "Low"
        if due > total_fee * Decimal('0.5'):
            risk = "High"
        elif due > 0:
            risk = "Medium"

        students_data.append({
            'name': student.name,
            'course': student.course.name,
            'total_fee': total_fee,
            'paid': paid,
            'due': due,
            'risk': risk
        })

    # Monthly revenue
    monthly_data = (
        FeePayment.objects
        .values('payment_date__month')
        .annotate(total=Sum('amount_paid'))
        .order_by('payment_date__month')
    )

    months = []
    revenues = []

    for item in monthly_data:
        months.append(calendar.month_name[item['payment_date__month']])
        revenues.append(float(item['total']))

    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_revenue': total_revenue,
        'total_due': total_due,
        'months': json.dumps(months),
        'revenues': json.dumps(revenues),
        'due_students': due_students,
        'students_data': students_data,
    }

    return render(request, 'core/dashboard.html', context)

def student_detail(request, id):
    student = get_object_or_404(Student, id=id)

    payments = FeePayment.objects.filter(student=student)

    total_paid = payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_fee = student.course.total_fee
    due = total_fee - total_paid

    context = {
        'student': student,
        'payments': payments,
        'total_paid': total_paid,
        'total_fee': total_fee,
        'due': due
    }

    return render(request, 'core/student_detail.html', context)

#Student overview

    total_students = Student.objects.count()
    total_courses = Course.objects.count()

    total_revenue = FeePayment.objects.aggregate(
        Sum('amount_paid')
    )['amount_paid__sum'] or 0

    students_data = []
    total_due = 0

    for student in Student.objects.all():
        total_fee = student.course.total_fee
        paid = FeePayment.objects.filter(student=student).aggregate(
            Sum('amount_paid')
        )['amount_paid__sum'] or 0

        due = total_fee - paid
        total_due += due

        # AI Risk
        if due > 100000:
            risk = "High"
        elif due > 50000:
            risk = "Medium"
        else:
            risk = "Low"

        students_data.append({
            'name': student.name,
            'course': student.course.name,
            'total_fee': total_fee,
            'paid': paid,
            'due': due,
            'risk': risk
        })

    monthly_data = (
        FeePayment.objects
        .values('payment_date__month')
        .annotate(total=Sum('amount_paid'))
        .order_by('payment_date__month')
    )

    months = []
    revenues = []

    for item in monthly_data:
        months.append(item['payment_date__month'])
        revenues.append(float(item['total']))

    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_revenue': total_revenue,
        'total_due': total_due,
        'months': json.dumps(months),
        'revenues': json.dumps(revenues),
        'students_data': students_data,
    }

    return render(request, 'core/dashboard.html', context)

#____________


from django.http import HttpResponse
import pandas as pd

def import_excel(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']

        # ✅ COURSES (optional)
        try:
            courses_df = pd.read_excel(file, sheet_name='Courses')

            for _, row in courses_df.iterrows():
                Course.objects.get_or_create(
                    name=row['name'],
                    defaults={
                        'duration': row.get('duration', 1),
                        'total_fee': row['total_fee']
                    }
                )
        except:
            pass

        file.seek(0)

        # ✅ STUDENTS
        students_df = pd.read_excel(file, sheet_name='Students')

        for _, row in students_df.iterrows():
            course = Course.objects.get(name=row['Course'])

            Student.objects.get_or_create(
                name=row['Name'],
                defaults={
                    'course': course
                }
            )

        file.seek(0)

        # ✅ PAYMENTS
        payments_df = pd.read_excel(file, sheet_name='Payments')

        for _, row in payments_df.iterrows():
            student = Student.objects.get(name=row['Student Name'])

            FeePayment.objects.create(
                student=student,
                amount_paid=row['Amount'],
                payment_date=row['Date'],
                remarks=row['Remarks']
            )

        return HttpResponse("✅ Data Imported Successfully")

    return render(request, 'core/import_excel.html')

#due students

due_students = []

students = Student.objects.select_related('course').all()

for student in students:
    total_fee = student.course.total_fee or 0

    paid = FeePayment.objects.filter(student=student).aggregate(
        Sum('amount_paid')
    )['amount_paid__sum'] or 0

    due = total_fee - paid

    if due > 0:
       due_students.append({
         'student_id': student.id,
         'name': student.name,
         'course': student.course.name,
          'due': due
        })
            
# Ai Report
def ai_report(request):
    high = 0
    medium = 0
    low = 0

    for student in Student.objects.all():
        total_fee = student.course.total_fee
        paid = FeePayment.objects.filter(student=student).aggregate(
            Sum('amount_paid')
        )['amount_paid__sum'] or 0

        due = total_fee - paid

        if due > total_fee * Decimal('0.5'):
            high += 1
        elif due > 0:
            medium += 1
        else:
            low += 1

    context = {
        'high': high,
        'medium': medium,
        'low': low,
    }

    return render(request, 'core/ai_report.html', context)

#Download Report
import pandas as pd
from django.http import HttpResponse

def export_excel(request):
    students = Student.objects.all()

    data = []

    for s in students:
        paid = FeePayment.objects.filter(student=s).aggregate(
            Sum('amount_paid')
        )['amount_paid__sum'] or 0

        total_fee = s.course.total_fee
        due = total_fee - paid

        data.append({
            'Name': s.name,
            'Course': s.course.name,
            'Total Fee': total_fee,
            'Paid': paid,
            'Due': due
        })

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="students_report.xlsx"'

    df.to_excel(response, index=False)

    return response

 #Add STUDENT 
def add_student(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        course_id = request.POST.get('course')

        course = Course.objects.get(id=course_id)

        Student.objects.create(
            name=name,
            email=email,
            phone=phone,
            course=course
        )

        return redirect('/')

    courses = Course.objects.all()
    return render(request, 'core/add_student.html', {'courses': courses})

    #add payment
def add_payment(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        amount = request.POST.get('amount')

        student = Student.objects.get(id=student_id)

        FeePayment.objects.create(
            student=student,
            amount_paid=amount
        )

        return redirect('/')

    students = Student.objects.all()
    return render(request, 'core/add_payment.html', {'students': students})
   
#Login page
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'core/login.html', {'error': 'Invalid login'})

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('/login/')

#Chatbot
from django.http import JsonResponse

def chatbot_api(request):
    msg = request.GET.get('msg', '').lower()

    # TOTAL STUDENTS
    if "total students" in msg:
        count = Student.objects.count()
        return JsonResponse({'reply': f"Total students are {count}"})

    # LIST STUDENTS
    elif "list students" in msg:
        names = list(Student.objects.values_list('name', flat=True))
        return JsonResponse({'reply': ", ".join(names[:10])})

    # COURSE FILTER
    elif "ai" in msg:
        students = Student.objects.filter(course__name__icontains="ai")
        names = list(students.values_list('name', flat=True))
        return JsonResponse({'reply': "AI Students: " + ", ".join(names[:5])})

    # DUE OF STUDENT
    elif "due" in msg:
        for student in Student.objects.all():
            if student.name.lower() in msg:
                paid = FeePayment.objects.filter(student=student).aggregate(
                    Sum('amount_paid')
                )['amount_paid__sum'] or 0

                due = student.course.total_fee - paid

                return JsonResponse({'reply': f"{student.name} due is ₹ {due}"})

        return JsonResponse({'reply': "Student not found"})

    return JsonResponse({'reply': "I didn't understand. Try asking about students or dues."})