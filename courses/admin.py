from django.contrib import admin
from .models import Category, Teacher, Course, Lesson, Booking

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'specialization', 'english_level', 'price_per_hour', 'rating')
    list_filter = ('english_level', 'specialization')
    search_fields = ('name', 'email', 'bio')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'teacher', 'english_level', 'price')
    list_filter = ('category', 'english_level')
    search_fields = ('title', 'description')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'teacher', 'lesson_type', 'english_level', 'date', 'time', 'status')
    list_filter = ('lesson_type', 'english_level', 'status')
    search_fields = ('title', 'teacher__name')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'teacher', 'date', 'time', 'lesson_type', 'status')
    list_filter = ('status', 'lesson_type')
    search_fields = ('user__username', 'teacher__name')
