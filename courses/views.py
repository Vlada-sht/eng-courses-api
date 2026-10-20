from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Teacher, Course
from .serializers import CategorySerializer, TeacherSerializer, CourseSerializer

def error_response(message, status_code):
    return Response({"error": message}, status=status_code)


class CategoryListCreateAPIView(APIView):
    def get(self, request):
        categories = Category.objects.all()
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

class CategoryDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(category).data)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)
        
        if category.courses.count() > 0:
            return error_response(f"Неможливо видалити категорію, оскільки до неї прив'язано курсів: {category.courses.count()}.", status.HTTP_409_CONFLICT)
        
        category.delete()
        return Response({"message": "Категорію видалено"}, status=status.HTTP_204_NO_CONTENT)

class TeacherListCreateAPIView(APIView):
    def get(self, request):
        teachers = Teacher.objects.all()
        return Response(TeacherSerializer(teachers, many=True).data)

    def post(self, request):
        serializer = TeacherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

class TeacherDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return None

    def get(self, request, pk):
        teacher = self.get_object(pk)
        if not teacher:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)
        return Response(TeacherSerializer(teacher).data)

    def put(self, request, pk):
        teacher = self.get_object(pk)
        if not teacher:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = TeacherSerializer(teacher, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        teacher = self.get_object(pk)
        if not teacher:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)
        
        if teacher.courses.count() > 0:
            return error_response(f"Неможливо видалити викладача, оскільки за ним закріплено курсів: {teacher.courses.count()}.", status.HTTP_409_CONFLICT)
        
        teacher.delete()
        return Response({"message": "Викладача видалено"}, status=status.HTTP_204_NO_CONTENT)


class CourseListCreateAPIView(APIView):
    def get(self, request):
        courses = Course.objects.all()
        return Response(CourseSerializer(courses, many=True).data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

class CourseDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return None

    def get(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        return Response(CourseSerializer(course).data)

    def put(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        course.delete()
        return Response({"message": "Курс видалено"}, status=status.HTTP_204_NO_CONTENT)