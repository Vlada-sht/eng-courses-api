from rest_framework import serializers
from .models import Category, Teacher, Course

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    teacher_name = serializers.ReadOnlyField(source='teacher.name')

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'level', 'price', 'category', 'teacher', 'category_name', 'teacher_name']