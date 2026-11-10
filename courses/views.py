from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from .models import Category, Teacher, Course, Lesson, Booking
from .serializers import (
    CategorySerializer,
    TeacherSerializer,
    TeacherDetailSerializer,
    CourseSerializer,
    LessonSerializer,
    BookingSerializer
)
from users.permissions import IsAuthenticatedOrReadOnly, IsAdminOrReadOnly, IsOwnerOrAdmin

def error_response(message, status_code, details=None):
    payload = {"error": message, "status_code": status_code}
    if details is not None:
        payload["details"] = details
    return Response(payload, status=status_code)


class CategoryListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        categories = Category.objects.all().order_by('name')
        return Response(CategorySerializer(categories, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response("Помилка валідації категорії", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


class CategoryDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(category).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації категорії", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def patch(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації категорії", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)

        linked_courses = category.courses.count()
        if linked_courses > 0:
            return error_response(
                f"Неможливо видалити категорію, оскільки до неї прив'язано курсів: {linked_courses}.",
                status.HTTP_409_CONFLICT,
                details={"linked_courses": linked_courses}
            )

        category.delete()
        return Response({"message": "Категорію успішно видалено", "status_code": 204}, status=status.HTTP_204_NO_CONTENT)


class TeacherListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = Teacher.objects.all().order_by('name')

        specialization = request.query_params.get('specialization')
        english_level = request.query_params.get('english_level') or request.query_params.get('level')
        search = request.query_params.get('search')

        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        if english_level:
            queryset = queryset.filter(english_level__iexact=english_level)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(bio__icontains=search) | Q(specialization__icontains=search)
            )

        serializer = TeacherSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TeacherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response("Помилка валідації даних викладача", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


class TeacherDetailAPIView(APIView):
    """
    Teacher profile endpoint returning detailed information including
    bio, rating, price per hour, english level, experience, courses, and lessons.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Teacher.objects.prefetch_related('courses', 'lessons').get(pk=pk)
        except Teacher.DoesNotExist:
            return None

    def get(self, request, pk):
        teacher = self.get_object(pk)
        if not teacher:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = TeacherDetailSerializer(teacher)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        teacher = self.get_object(pk)
        if not teacher:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = TeacherSerializer(teacher, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(TeacherDetailSerializer(teacher).data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації даних викладача", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def patch(self, request, pk):
        teacher = self.get_object(pk)
        if not teacher:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = TeacherSerializer(teacher, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TeacherDetailSerializer(teacher).data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації даних викладача", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def delete(self, request, pk):
        teacher = self.get_object(pk)
        if not teacher:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)

        courses_count = teacher.courses.count()
        lessons_count = teacher.lessons.count()
        if courses_count > 0 or lessons_count > 0:
            return error_response(
                f"Неможливо видалити викладача, оскільки за ним закріплено курсів: {courses_count}, занять: {lessons_count}.",
                status.HTTP_409_CONFLICT,
                details={"courses_count": courses_count, "lessons_count": lessons_count}
            )

        teacher.delete()
        return Response({"message": "Викладача успішно видалено", "status_code": 204}, status=status.HTTP_204_NO_CONTENT)


class TeacherLessonsAPIView(APIView):
    """
    Specific endpoint to retrieve lessons for a given teacher by ID
    with filtering by lesson type (lesson_type).
    Example: GET /api/teachers/1/lessons/?lesson_type=Speaking Club
    """
    permission_classes = [AllowAny]

    def get(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except Teacher.DoesNotExist:
            return error_response("Викладача не знайдено", status.HTTP_404_NOT_FOUND)

        lessons = teacher.lessons.all().order_by('date', 'time')

        lesson_type = request.query_params.get('lesson_type')
        english_level = request.query_params.get('english_level') or request.query_params.get('level')
        status_filter = request.query_params.get('status')

        if lesson_type:
            lessons = lessons.filter(lesson_type__icontains=lesson_type)
        if english_level:
            lessons = lessons.filter(english_level__iexact=english_level)
        if status_filter:
            lessons = lessons.filter(status__iexact=status_filter)

        serializer = LessonSerializer(lessons, many=True)
        return Response({
            "teacher_id": teacher.id,
            "teacher_name": teacher.name,
            "count": lessons.count(),
            "lessons": serializer.data
        }, status=status.HTTP_200_OK)


class CourseListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = Course.objects.select_related('category', 'teacher').all().order_by('title')

        category_id = request.query_params.get('category') or request.query_params.get('category_id')
        teacher_id = request.query_params.get('teacher') or request.query_params.get('teacher_id')
        english_level = request.query_params.get('english_level') or request.query_params.get('level')
        search = request.query_params.get('search')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if english_level:
            queryset = queryset.filter(Q(level__iexact=english_level) | Q(english_level__iexact=english_level))
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response("Помилка валідації даних курсу", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


class CourseDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Course.objects.select_related('category', 'teacher').get(pk=pk)
        except Course.DoesNotExist:
            return None

    def get(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        return Response(CourseSerializer(course).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації даних курсу", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def patch(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації даних курсу", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def delete(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        course.delete()
        return Response({"message": "Курс успішно видалено", "status_code": 204}, status=status.HTTP_204_NO_CONTENT)


class LessonListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = Lesson.objects.select_related('teacher', 'course').all().order_by('date', 'time')

        teacher_id = request.query_params.get('teacher_id')
        lesson_type = request.query_params.get('lesson_type')
        english_level = request.query_params.get('english_level') or request.query_params.get('level')

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if lesson_type:
            queryset = queryset.filter(lesson_type__icontains=lesson_type)
        if english_level:
            queryset = queryset.filter(english_level__iexact=english_level)

        serializer = LessonSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response("Помилка валідації заняття", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


class LessonDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Lesson.objects.select_related('teacher', 'course').get(pk=pk)
        except Lesson.DoesNotExist:
            return None

    def get(self, request, pk):
        lesson = self.get_object(pk)
        if not lesson:
            return error_response("Заняття не знайдено", status.HTTP_404_NOT_FOUND)
        return Response(LessonSerializer(lesson).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        lesson = self.get_object(pk)
        if not lesson:
            return error_response("Заняття не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = LessonSerializer(lesson, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації заняття", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def delete(self, request, pk):
        lesson = self.get_object(pk)
        if not lesson:
            return error_response("Заняття не знайдено", status.HTTP_404_NOT_FOUND)
        lesson.delete()
        return Response({"message": "Заняття успішно видалено", "status_code": 204}, status=status.HTTP_204_NO_CONTENT)


class BookingListCreateAPIView(APIView):
    """
    Endpoint for booking lessons.
    POST /api/bookings/ requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            bookings = Booking.objects.select_related('user', 'teacher', 'lesson').all().order_by('-date')
        else:
            bookings = Booking.objects.select_related('teacher', 'lesson').filter(user=request.user).order_by('-date')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        teacher_id = request.data.get('teacher_id')
        date = request.data.get('date')
        time = request.data.get('time')
        lesson_type = request.data.get('lesson_type', 'Speaking Club')
        lesson_id = request.data.get('lesson_id')
        notes = request.data.get('notes', '')

        if not teacher_id or not date or not time:
            return error_response(
                "Поля teacher_id, date та time є обов'язковими для бронювання.",
                status.HTTP_400_BAD_REQUEST,
                details={"required_fields": ["teacher_id", "date", "time"]}
            )

        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except Teacher.DoesNotExist:
            return error_response("Викладача з вказаним ID не знайдено.", status.HTTP_404_NOT_FOUND)

        lesson = None
        if lesson_id:
            try:
                lesson = Lesson.objects.get(pk=lesson_id, teacher=teacher)
            except Lesson.DoesNotExist:
                return error_response("Вказане заняття для цього викладача не знайдено.", status.HTTP_404_NOT_FOUND)

        booking = Booking.objects.create(
            user=request.user,
            teacher=teacher,
            lesson=lesson,
            date=date,
            time=time,
            lesson_type=lesson_type,
            notes=notes,
            status='confirmed'
        )

        return Response({
            "id": booking.id,
            "booking_id": booking.id,
            "teacher_id": teacher.id,
            "teacher_name": teacher.name,
            "date": str(booking.date),
            "time": str(booking.time),
            "lesson_type": booking.lesson_type,
            "status": booking.status,
            "message": "Заняття успішно заброньовано"
        }, status=status.HTTP_201_CREATED)


class BookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            if user.is_staff:
                return Booking.objects.select_related('teacher', 'lesson').get(pk=pk)
            return Booking.objects.select_related('teacher', 'lesson').get(pk=pk, user=user)
        except Booking.DoesNotExist:
            return None

    def get(self, request, pk):
        booking = self.get_object(pk, request.user)
        if not booking:
            return error_response("Бронювання не знайдено або доступ заборонено.", status.HTTP_404_NOT_FOUND)
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        booking = self.get_object(pk, request.user)
        if not booking:
            return error_response("Бронювання не знайдено або доступ заборонено.", status.HTTP_404_NOT_FOUND)
        booking.status = 'cancelled'
        booking.save()
        return Response({
            "message": "Бронювання успішно скасовано.",
            "booking_id": booking.id,
            "status": booking.status
        }, status=status.HTTP_200_OK)
