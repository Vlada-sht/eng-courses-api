from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Teacher, Course, Lesson, Booking

class CourseAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="student1", email="student1@example.com", password="Password123!")
        self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="AdminPassword123!")

        self.category = Category.objects.create(name="Exam Prep", description="Prepare for international tests")
        self.teacher = Teacher.objects.create(
            name="Lily Snape",
            email="lily@example.com",
            bio="CELTA certified tutor with 5 years of experience",
            specialization="IELTS Prep",
            price_per_hour=450.00,
            rating=4.95,
            english_level="C2",
            experience_years=5
        )
        self.course = Course.objects.create(
            title="IELTS Academic Masterclass",
            description="Intensive prep course for IELTS Academic 7.5+",
            level="B2",
            english_level="B2",
            price=2500.00,
            category=self.category,
            teacher=self.teacher
        )
        self.lesson1 = Lesson.objects.create(
            teacher=self.teacher,
            course=self.course,
            title="Speaking Practice: Part 2 & 3",
            lesson_type="Speaking Club",
            english_level="B2",
            date="2026-11-25",
            time="16:00:00",
            price=350.00
        )
        self.lesson2 = Lesson.objects.create(
            teacher=self.teacher,
            course=self.course,
            title="Writing Task 2 Essay Analysis",
            lesson_type="Grammar Intensive",
            english_level="C1",
            date="2026-11-26",
            time="17:00:00",
            price=400.00
        )

    def test_teacher_list_and_filters(self):
        # List teachers
        response = self.client.get('/api/teachers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["english_level"], "C2")

        # Filter by specialization
        response = self.client.get('/api/teachers/?specialization=IELTS')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Filter by non-existing specialization
        response = self.client.get('/api/teachers/?specialization=French')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_teacher_detail_profile(self):
        response = self.client.get(f'/api/teachers/{self.teacher.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Lily Snape")
        self.assertEqual(response.data["english_level"], "C2")
        self.assertEqual(response.data["specialization"], "IELTS Prep")
        self.assertIn("courses", response.data)
        self.assertIn("lessons", response.data)
        self.assertEqual(len(response.data["courses"]), 1)
        self.assertEqual(len(response.data["lessons"]), 2)

    def test_teacher_lessons_endpoint_filtered_by_lesson_type(self):
        # Specific endpoint: /api/teachers/<id>/lessons/?lesson_type=Speaking Club
        url = f'/api/teachers/{self.teacher.id}/lessons/?lesson_type=Speaking Club'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["teacher_id"], self.teacher.id)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["lessons"][0]["lesson_type"], "Speaking Club")
        self.assertEqual(response.data["lessons"][0]["english_level"], "B2")

        # Non-existing teacher 404
        response_404 = self.client.get('/api/teachers/9999/lessons/')
        self.assertEqual(response_404.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response_404.data)

    def test_conflict_409_on_deleting_teacher_with_dependencies(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/teachers/{self.teacher.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error", response.data)

    def test_conflict_409_on_deleting_category_with_courses(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error", response.data)

    def test_booking_creation_authenticated(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "teacher_id": self.teacher.id,
            "date": "2026-12-01",
            "time": "14:00",
            "lesson_type": "Speaking Club"
        }
        response = self.client.post('/api/bookings/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "confirmed")
        self.assertEqual(response.data["teacher_id"], self.teacher.id)

        # Check user's bookings endpoint
        my_bookings_res = self.client.get('/api/users/me/bookings/')
        self.assertEqual(my_bookings_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(my_bookings_res.data), 1)

    def test_unauthenticated_booking_401(self):
        payload = {
            "teacher_id": self.teacher.id,
            "date": "2026-12-01",
            "time": "14:00"
        }
        response = self.client.post('/api/bookings/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)
