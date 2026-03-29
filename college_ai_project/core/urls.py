from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('student/<int:id>/', views.student_detail, name='student_detail'),
    path('import-excel/', views.import_excel),
    path('ai-report/', views.ai_report, name='ai_report'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('add-student/', views.add_student, name='add_student'),
    path('add-payment/', views.add_payment, name='add_payment'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('chatbot/', views.chatbot_api, name='chatbot_api'),
    ]
