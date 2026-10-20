from django.urls import path
from .views import (
    CategoryListCreateAPIView, CategoryDetailAPIView,
    TeacherListCreateAPIView, TeacherDetailAPIView,
    CourseListCreateAPIView, CourseDetailAPIView
)

urlpatterns = [
    path('categories/', CategoryListCreateAPIView.as_view()),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view()),
    path('teachers/', TeacherListCreateAPIView.as_view()),
    path('teachers/<int:pk>/', TeacherDetailAPIView.as_view()),
    path('courses/', CourseListCreateAPIView.as_view()),
    path('courses/<int:pk>/', CourseDetailAPIView.as_view()),
]