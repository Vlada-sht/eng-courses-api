import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes,
)

from .models import Category, Teacher, Course, Lesson, Booking
from .serializers import (
    CategorySerializer,
    TeacherSerializer,
    TeacherDetailSerializer,
    CourseSerializer,
    LessonSerializer,
    BookingSerializer,
)
from users.permissions import IsAuthenticatedOrReadOnly, IsAdminOrReadOnly, IsOwnerOrAdmin

logger = logging.getLogger('courses')


def error_response(message, status_code, details=None):
    payload = {"error": message, "status_code": status_code}
    if details is not None:
        payload["details"] = details
    return Response(payload, status=status_code)


@extend_schema(tags=['Categories'])
class CategoryListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        categories = Category.objects.all().order_by('name')
        return Response(CategorySerializer(categories, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            logger.info("User '%s' created category id=%s ('%s')", request.user, category.id, category.name)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning("Category validation failed by user '%s': %s", request.user, serializer.errors)
        return error_response("Помилка валідації категорії", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


@extend_schema(tags=['Categories'])
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
            logger.info("User '%s' updated category id=%s", request.user, pk)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації категорії", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def patch(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info("User '%s' partially updated category id=%s", request.user, pk)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return error_response("Помилка валідації категорії", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return error_response("Категорію не знайдено", status.HTTP_404_NOT_FOUND)

        linked_courses = category.courses.count()
        if linked_courses > 0:
            logger.warning("Failed to delete category id=%s: has %s linked courses", pk, linked_courses)
            return error_response(
                f"Неможливо видалити категорію, оскільки до неї прив'язано курсів: {linked_courses}.",
                status.HTTP_409_CONFLICT,
                details={"linked_courses": linked_courses}
            )

        category.delete()
        logger.info("User '%s' deleted category id=%s", request.user, pk)
        return Response({"message": "Категорію успішно видалено", "status_code": 204}, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Teachers'])
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
            teacher = serializer.save()
            logger.info("User '%s' created teacher id=%s ('%s')", request.user, teacher.id, teacher.name)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response("Помилка валідації даних викладача", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


@extend_schema(tags=['Teachers'])
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


@extend_schema(tags=['Teachers'])
class TeacherLessonsAPIView(APIView):
    """
    Specific endpoint to retrieve lessons for a given teacher by ID
    with filtering by lesson type (lesson_type).
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


@extend_schema(tags=['Courses'])
class CourseListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Отримати список курсів",
        description="Повертає перелік усіх курсів англійської мови з можливістю фільтрації. Доступно без автентифікації.",
        parameters=[
            OpenApiParameter('category', OpenApiTypes.INT, description='Фільтрація за ID категорії'),
            OpenApiParameter('teacher', OpenApiTypes.INT, description='Фільтрація за ID викладача'),
            OpenApiParameter('english_level', OpenApiTypes.STR, description='Рівень володіння англійською (напр. B1, B2, C1)'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Пошук за назвою або описом курсу'),
        ],
        responses={200: CourseSerializer(many=True)},
    )
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

        logger.debug("Fetched %s courses (filters: category=%s, teacher=%s, level=%s, search=%s)",
                     queryset.count(), category_id, teacher_id, english_level, search)
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Створити новий курс",
        description="Створює новий курс англійської мови. Вимагає JWT-автентифікації (Bearer token).",
        request=CourseSerializer,
        responses={
            201: CourseSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Приклад створення курсу',
                value={
                    "title": "Business English Pro",
                    "description": "Інтенсивний курс ділової англійської для IT-фахівців",
                    "level": "B2",
                    "english_level": "B2",
                    "price": "3200.00",
                    "category": 1,
                    "teacher": 1
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            course = serializer.save()
            logger.info("User '%s' created course id=%s ('%s')", request.user, course.id, course.title)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning("Course creation validation failed for user '%s': %s", request.user, serializer.errors)
        return error_response("Помилка валідації даних курсу", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


@extend_schema(tags=['Courses'])
class CourseDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Course.objects.select_related('category', 'teacher').get(pk=pk)
        except Course.DoesNotExist:
            return None

    @extend_schema(
        summary="Деталі курсу",
        description="Повертає детальну інформацію про курс за його ID. Доступно публічно.",
        responses={200: CourseSerializer, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request, pk):
        course = self.get_object(pk)
        if not course:
            logger.warning("Course id=%s not found (GET)", pk)
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        return Response(CourseSerializer(course).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Повністю оновити курс (PUT)",
        description="Повне оновлення полів курсу за ID. Вимагає JWT-автентифікації.",
        request=CourseSerializer,
        responses={200: CourseSerializer, 400: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def put(self, request, pk):
        course = self.get_object(pk)
        if not course:
            logger.warning("Course id=%s not found for PUT by user '%s'", pk, request.user)
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("User '%s' fully updated course id=%s", request.user, pk)
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.warning("Course PUT validation failed for id=%s by user '%s': %s", pk, request.user, serializer.errors)
        return error_response("Помилка валідації даних курсу", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    @extend_schema(
        summary="Частково оновити курс (PATCH)",
        description="Часткове оновлення вибраних полів курсу за ID. Вимагає JWT-автентифікації.",
        request=CourseSerializer,
        responses={200: CourseSerializer, 400: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                'Оновлення ціни курсу',
                value={"price": "2900.00"},
                request_only=True,
            )
        ],
    )
    def patch(self, request, pk):
        course = self.get_object(pk)
        if not course:
            logger.warning("Course id=%s not found for PATCH by user '%s'", pk, request.user)
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info("User '%s' partially updated course id=%s", request.user, pk)
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.warning("Course PATCH validation failed for id=%s by user '%s': %s", pk, request.user, serializer.errors)
        return error_response("Помилка валідації даних курсу", status.HTTP_400_BAD_REQUEST, details=serializer.errors)

    @extend_schema(
        summary="Видалити курс",
        description="Видаляє курс за його ID. Вимагає JWT-автентифікації.",
        responses={204: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def delete(self, request, pk):
        course = self.get_object(pk)
        if not course:
            logger.warning("Course id=%s not found for DELETE by user '%s'", pk, request.user)
            return error_response("Курс не знайдено", status.HTTP_404_NOT_FOUND)
        course.delete()
        logger.info("User '%s' deleted course id=%s", request.user, pk)
        return Response({"message": "Курс успішно видалено", "status_code": 204}, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Lessons'])
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
            lesson = serializer.save()
            logger.info("User '%s' created lesson id=%s", request.user, lesson.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return error_response("Помилка валідації заняття", status.HTTP_400_BAD_REQUEST, details=serializer.errors)


@extend_schema(tags=['Lessons'])
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


@extend_schema(tags=['Bookings'])
class BookingListCreateAPIView(APIView):
    """
    Endpoint for booking lessons.
    POST /api/bookings/ requires authentication.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Список бронювань користувача",
        description=(
            "Повертає список бронювань. Звичайний користувач бачить лише власні бронювання, "
            "а адміністратор (is_staff=True) — усі бронювання системи."
        ),
        responses={200: BookingSerializer(many=True), 401: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        if request.user.is_staff:
            bookings = Booking.objects.select_related('user', 'teacher', 'lesson').all().order_by('-date')
            logger.debug("Admin '%s' fetched all %s bookings", request.user, bookings.count())
        else:
            bookings = Booking.objects.select_related('teacher', 'lesson').filter(user=request.user).order_by('-date')
            logger.debug("User '%s' fetched %s personal bookings", request.user, bookings.count())
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Створити бронювання заняття",
        description="Бронює індивідуальне або групове заняття з викладачем для поточного авторизованого користувача.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'teacher_id': {'type': 'integer', 'example': 1},
                    'lesson_id': {'type': 'integer', 'nullable': True, 'example': 1},
                    'date': {'type': 'string', 'format': 'date', 'example': '2026-12-01'},
                    'time': {'type': 'string', 'format': 'time', 'example': '15:00:00'},
                    'lesson_type': {'type': 'string', 'example': 'Speaking Club'},
                    'notes': {'type': 'string', 'example': 'Хочу попрактикувати розмовну мову'},
                },
                'required': ['teacher_id', 'date', 'time'],
            }
        },
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):
        teacher_id = request.data.get('teacher_id')
        date = request.data.get('date')
        time = request.data.get('time')
        lesson_type = request.data.get('lesson_type', 'Speaking Club')
        lesson_id = request.data.get('lesson_id')
        notes = request.data.get('notes', '')

        if not teacher_id or not date or not time:
            logger.warning("Booking creation failed for user '%s': missing required fields", request.user)
            return error_response(
                "Поля teacher_id, date та time є обов'язковими для бронювання.",
                status.HTTP_400_BAD_REQUEST,
                details={"required_fields": ["teacher_id", "date", "time"]}
            )

        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except Teacher.DoesNotExist:
            logger.warning("Booking creation failed for user '%s': teacher_id=%s not found", request.user, teacher_id)
            return error_response("Викладача з вказаним ID не знайдено.", status.HTTP_404_NOT_FOUND)

        lesson = None
        if lesson_id:
            try:
                lesson = Lesson.objects.get(pk=lesson_id, teacher=teacher)
            except Lesson.DoesNotExist:
                logger.warning("Booking creation failed for user '%s': lesson_id=%s not found for teacher_id=%s",
                               request.user, lesson_id, teacher_id)
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
        logger.info("User '%s' created booking id=%s with teacher_id=%s on %s %s",
                    request.user, booking.id, teacher.id, date, time)

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


@extend_schema(tags=['Bookings'])
class BookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            if user.is_staff:
                return Booking.objects.select_related('teacher', 'lesson').get(pk=pk)
            return Booking.objects.select_related('teacher', 'lesson').get(pk=pk, user=user)
        except Booking.DoesNotExist:
            return None

    @extend_schema(
        summary="Деталі бронювання",
        description="Повертає деталі бронювання. Користувач має доступ лише до власних записів, адміністратор — до будь-яких.",
        responses={200: BookingSerializer, 401: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request, pk):
        booking = self.get_object(pk, request.user)
        if not booking:
            logger.warning("User '%s' denied or not found for booking id=%s (GET)", request.user, pk)
            return error_response("Бронювання не знайдено або доступ заборонено.", status.HTTP_404_NOT_FOUND)
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Скасувати бронювання",
        description="Змінює статус бронювання на 'cancelled'. Доступно власнику бронювання або адміністратору.",
        responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def delete(self, request, pk):
        booking = self.get_object(pk, request.user)
        if not booking:
            logger.warning("User '%s' denied or not found for booking id=%s (DELETE)", request.user, pk)
            return error_response("Бронювання не знайдено або доступ заборонено.", status.HTTP_404_NOT_FOUND)
        booking.status = 'cancelled'
        booking.save()
        logger.info("User '%s' cancelled booking id=%s", request.user, booking.id)
        return Response({
            "message": "Бронювання успішно скасовано.",
            "booking_id": booking.id,
            "status": booking.status
        }, status=status.HTTP_200_OK)