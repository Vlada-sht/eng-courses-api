from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Teacher, Course, Lesson, Booking

User = get_user_model()


class CourseAPITests(APITestCase):
    """
    Автоматизовані тести для ресурсу Courses:
    - позитивні CRUD-сценарії (GET, POST, PUT, PATCH, DELETE) та фільтрація;
    - негативні сценарії (400 при невалідних даних, 401 без токена, 404 для неіснуючого ID).
    """

    def setUp(self):
        # Фікстури користувачів
        self.user = User.objects.create_user(
            username='teacher_user',
            email='teacher@example.com',
            password='StrongPassword123!'
        )

        # Фікстури категорії, викладача та курсу
        self.category = Category.objects.create(
            name='Business English',
            description='Курси ділової англійської мови'
        )
        self.teacher = Teacher.objects.create(
            name='Олена Коваленко',
            email='olena.teacher@example.com',
            specialization='Business English',
            english_level='C2',
            price_per_hour='500.00'
        )
        self.course = Course.objects.create(
            title='English for IT',
            description='Розмовна та технічна англійська для розробників',
            level='B2',
            english_level='B2',
            price='2800.00',
            category=self.category,
            teacher=self.teacher
        )

        self.list_url = reverse('course-list-create')
        self.detail_url = reverse('course-detail', kwargs={'pk': self.course.pk})

    # --- Позитивні сценарії ---

    def test_get_courses_list_public(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'English for IT')

    def test_filter_courses_by_level_and_search(self):
        response = self.client.get(self.list_url, {'english_level': 'B2', 'search': 'IT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        empty_response = self.client.get(self.list_url, {'english_level': 'C1'})
        self.assertEqual(empty_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(empty_response.data), 0)

    def test_get_course_detail_public(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'English for IT')
        self.assertEqual(response.data['teacher_name'], 'Олена Коваленко')

    def test_create_course_authenticated(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'title': 'IELTS Academic Preparation',
            'description': 'Інтенсивна підготовка до складання іспиту IELTS',
            'level': 'C1',
            'english_level': 'C1',
            'price': '3500.00',
            'category': self.category.id,
            'teacher': self.teacher.id,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 2)
        self.assertEqual(response.data['title'], 'IELTS Academic Preparation')

    def test_full_update_course_put_authenticated(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'title': 'English for IT Advanced',
            'description': 'Оновлена програма для Senior-спеціалістів',
            'level': 'C1',
            'english_level': 'C1',
            'price': '3200.00',
            'category': self.category.id,
            'teacher': self.teacher.id,
        }
        response = self.client.put(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'English for IT Advanced')
        self.assertEqual(self.course.level, 'C1')

    def test_partial_update_course_patch_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.detail_url, {'price': '2999.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(str(self.course.price), '2999.00')

    def test_delete_course_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 0)

    # --- Негативні сценарії ---

    def test_create_course_unauthenticated_fails(self):
        payload = {
            'title': 'Unauthorized Course',
            'description': 'Не має створитися без JWT',
            'price': '1500.00',
            'category': self.category.id,
            'teacher': self.teacher.id,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Course.objects.count(), 1)

    def test_create_course_invalid_data_fails(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'title': '',
            'price': 'invalid-price',
            'category': 99999,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_course_unauthenticated_fails(self):
        response = self.client.patch(self.detail_url, {'price': '100.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_nonexistent_course_returns_404(self):
        url = reverse('course-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_course_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('course-detail', kwargs={'pk': 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BookingRoleAndPermissionsAPITests(APITestCase):
    """
    Тести розмежування прав доступу та ролей на прикладі ресурсу Bookings:
    - звичайний студент бачить і скасовує лише власні бронювання;
    - адміністратор (is_staff=True) має доступ до всіх бронювань;
    - неавторизовані запити відхиляються зі статусом 401.
    """

    def setUp(self):
        self.student_one = User.objects.create_user(
            username='student_one',
            password='Password123!'
        )
        self.student_two = User.objects.create_user(
            username='student_two',
            password='Password123!'
        )
        self.admin_user = User.objects.create_user(
            username='admin_user',
            password='AdminPassword123!',
            is_staff=True
        )

        self.teacher = Teacher.objects.create(
            name='Марко Бондаренко',
            email='marko@example.com',
            specialization='Speaking Club',
            english_level='C1'
        )
        self.lesson = Lesson.objects.create(
            teacher=self.teacher,
            title='Weekend Speaking Club',
            lesson_type='Speaking Club',
            english_level='B2',
            date='2026-12-10',
            time='18:00:00'
        )

        self.booking_one = Booking.objects.create(
            user=self.student_one,
            teacher=self.teacher,
            lesson=self.lesson,
            date='2026-12-10',
            time='18:00:00'
        )
        self.booking_two = Booking.objects.create(
            user=self.student_two,
            teacher=self.teacher,
            date='2026-12-12',
            time='14:00:00'
        )

        self.bookings_url = reverse('booking-list-create')

    def test_unauthenticated_cannot_access_bookings(self):
        response = self.client.get(self.bookings_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_sees_only_own_bookings(self):
        self.client.force_authenticate(user=self.student_one)
        response = self.client.get(self.bookings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.booking_one.id)

    def test_admin_sees_all_bookings(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.bookings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_booking_success(self):
        self.client.force_authenticate(user=self.student_one)
        payload = {
            'teacher_id': self.teacher.id,
            'lesson_id': self.lesson.id,
            'date': '2026-12-15',
            'time': '16:30:00',
            'lesson_type': 'Individual',
            'notes': 'Підготовка до співбесіди'
        }
        response = self.client.post(self.bookings_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.filter(user=self.student_one).count(), 2)

    def test_create_booking_missing_required_fields_fails(self):
        self.client.force_authenticate(user=self.student_one)
        response = self.client.post(self.bookings_url, {'teacher_id': self.teacher.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_access_or_cancel_other_student_booking(self):
        self.client.force_authenticate(user=self.student_one)
        other_booking_url = reverse('booking-detail', kwargs={'pk': self.booking_two.pk})

        get_resp = self.client.get(other_booking_url)
        self.assertEqual(get_resp.status_code, status.HTTP_404_NOT_FOUND)

        del_resp = self.client.delete(other_booking_url)
        self.assertEqual(del_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_can_cancel_own_booking(self):
        self.client.force_authenticate(user=self.student_one)
        own_booking_url = reverse('booking-detail', kwargs={'pk': self.booking_one.pk})
        response = self.client.delete(own_booking_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking_one.refresh_from_db()
        self.assertEqual(self.booking_one.status, 'cancelled')

    def test_admin_can_cancel_any_booking(self):
        self.client.force_authenticate(user=self.admin_user)
        other_booking_url = reverse('booking-detail', kwargs={'pk': self.booking_two.pk})
        response = self.client.delete(other_booking_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking_two.refresh_from_db()
        self.assertEqual(self.booking_two.status, 'cancelled')