from django.urls import path
from .views import (
    CategoryListCreateAPIView, CategoryDetailAPIView,
    TeacherListCreateAPIView, TeacherDetailAPIView, TeacherLessonsAPIView,
    CourseListCreateAPIView, CourseDetailAPIView,
    LessonListCreateAPIView, LessonDetailAPIView,
    BookingListCreateAPIView, BookingDetailAPIView
)

urlpatterns = [
    # Categories
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view(), name='category-detail'),

    # Teachers
    path('teachers/', TeacherListCreateAPIView.as_view(), name='teacher-list-create'),
    path('teachers/<int:pk>/', TeacherDetailAPIView.as_view(), name='teacher-detail'),
    path('teachers/<int:pk>/profile/', TeacherDetailAPIView.as_view(), name='teacher-profile'),
    path('teachers/<int:teacher_id>/lessons/', TeacherLessonsAPIView.as_view(), name='teacher-lessons'),

    # Courses
    path('courses/', CourseListCreateAPIView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseDetailAPIView.as_view(), name='course-detail'),

    # Lessons
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonDetailAPIView.as_view(), name='lesson-detail'),

    # Bookings
    path('bookings/', BookingListCreateAPIView.as_view(), name='booking-list-create'),
    path('bookings', BookingListCreateAPIView.as_view()),
    path('bookings/<int:pk>/', BookingDetailAPIView.as_view(), name='booking-detail'),
]
