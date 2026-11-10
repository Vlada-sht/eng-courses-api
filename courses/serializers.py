from rest_framework import serializers
from .models import Category, Teacher, Course, Lesson, Booking

class CategorySerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(source='courses.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'courses_count']


class CourseShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'level', 'english_level', 'price']


class LessonSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField(source='teacher.name')
    course_title = serializers.ReadOnlyField(source='course.title')

    class Meta:
        model = Lesson
        fields = [
            'id', 'teacher', 'teacher_name', 'course', 'course_title',
            'title', 'lesson_type', 'english_level', 'date', 'time',
            'duration_minutes', 'price', 'status', 'description', 'created_at'
        ]


class TeacherSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(source='courses.count', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'name', 'email', 'bio', 'specialization',
            'price_per_hour', 'rating', 'english_level', 'experience_years',
            'courses_count'
        ]


class TeacherDetailSerializer(serializers.ModelSerializer):
    courses = CourseShortSerializer(many=True, read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)
    courses_count = serializers.IntegerField(source='courses.count', read_only=True)
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'name', 'email', 'bio', 'specialization',
            'price_per_hour', 'rating', 'english_level', 'experience_years',
            'courses_count', 'lessons_count', 'courses', 'lessons'
        ]


class CourseSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    teacher_name = serializers.ReadOnlyField(source='teacher.name')

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'level', 'english_level',
            'price', 'category', 'teacher', 'category_name', 'teacher_name'
        ]


class BookingSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField(source='teacher.name')
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'user_username', 'teacher', 'teacher_name',
            'lesson', 'date', 'time', 'lesson_type', 'status', 'notes', 'created_at'
        ]
        read_only_fields = ['user', 'status', 'created_at']
