from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile
from courses.models import Category, Teacher, Course, Lesson, Booking
from django.utils import timezone
from datetime import date, time, timedelta

class Command(BaseCommand):
    help = 'Seeds database with realistic initial test data'

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # 1. Superuser & Student
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@engcourses.com',
                'first_name': 'Адміністратор',
                'last_name': 'Системи',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('Admin1234!')
            admin_user.save()
            admin_user.profile.role = 'admin'
            admin_user.profile.english_level = 'C2'
            admin_user.profile.save()

        student_user, s_created = User.objects.get_or_create(
            username='student',
            defaults={
                'email': 'student@gmail.com',
                'first_name': 'Владислава',
                'last_name': 'Штомпіль',
                'is_staff': False,
            }
        )
        if s_created:
            student_user.set_password('Student1234!')
            student_user.save()
            student_user.profile.role = 'student'
            student_user.profile.english_level = 'B2'
            student_user.profile.save()

        # 2. Categories
        exam_cat, _ = Category.objects.get_or_create(
            name='Підготовка до іспитів (IELTS / TOEFL)',
            defaults={'description': 'Комплексна підготовка до міжнародних тестів з носіями та сертифікованими викладачами'}
        )
        speaking_cat, _ = Category.objects.get_or_create(
            name='Speaking Clubs (Розмовні клуби)',
            defaults={'description': 'Практика вільного мовлення, подолання мовного бар’єру, активна лексика'}
        )
        business_cat, _ = Category.objects.get_or_create(
            name='Business English (Ділова англійська)',
            defaults={'description': 'Англійська для кар’єри, IT, переговорів та ділового листування'}
        )
        general_cat, _ = Category.objects.get_or_create(
            name='General English (Загальний курс)',
            defaults={'description': 'Покращення граматики, розширення словникового запасу, читання та аудіювання'}
        )

        # 3. Teachers
        teacher1, _ = Teacher.objects.get_or_create(
            email='lily.snape@engcourses.com',
            defaults={
                'name': 'Lily Snape',
                'bio': 'Сертифікований викладач CELTA з 5-річним досвідом підготовки студентів до IELTS на бал 7.5+.',
                'specialization': 'IELTS Prep',
                'price_per_hour': 450.00,
                'rating': 4.95,
                'english_level': 'C2',
                'experience_years': 5
            }
        )
        teacher2, _ = Teacher.objects.get_or_create(
            email='john.smith@engcourses.com',
            defaults={
                'name': 'John Smith',
                'bio': 'Носій мови (Лондон, Велика Британія). Понад 8 років досвіду корпоративного навчання для IT-компаній.',
                'specialization': 'Business English',
                'price_per_hour': 600.00,
                'rating': 5.00,
                'english_level': 'Native',
                'experience_years': 8
            }
        )
        teacher3, _ = Teacher.objects.get_or_create(
            email='olena.melnyk@engcourses.com',
            defaults={
                'name': 'Олена Мельник',
                'bio': 'Магістр філології, ведуча щотижневих розмовних клубів з акцентом на подолання мовного бар\'єру.',
                'specialization': 'Speaking Club',
                'price_per_hour': 380.00,
                'rating': 4.88,
                'english_level': 'C1',
                'experience_years': 4
            }
        )

        # 4. Courses
        course1, _ = Course.objects.get_or_create(
            title='IELTS Academic Masterclass',
            teacher=teacher1,
            defaults={
                'description': 'Інтенсивний курс підготовки до всіх секцій іспиту IELTS Academic: Writing, Speaking, Reading, Listening.',
                'level': 'B2',
                'english_level': 'B2',
                'price': 4200.00,
                'category': exam_cat
            }
        )
        course2, _ = Course.objects.get_or_create(
            title='English for IT & Tech Standups',
            teacher=teacher2,
            defaults={
                'description': 'Практичний курс англійської для розробників, PM та дизайнерів. Робота в команді та презентація демо.',
                'level': 'B2',
                'english_level': 'B2',
                'price': 4800.00,
                'category': business_cat
            }
        )
        course3, _ = Course.objects.get_or_create(
            title='Weekend Conversational Club: B1-B2',
            teacher=teacher3,
            defaults={
                'description': 'Дискусії на актуальні теми, перегляд TED Talks, розбір сучасної лексики та ідіом.',
                'level': 'B1',
                'english_level': 'B1',
                'price': 1600.00,
                'category': speaking_cat
            }
        )

        # 5. Lessons
        today = date.today()
        lesson1, _ = Lesson.objects.get_or_create(
            teacher=teacher1,
            title='IELTS Speaking Part 2 & 3: Deep Dive',
            defaults={
                'course': course1,
                'lesson_type': 'Speaking Club',
                'english_level': 'B2',
                'date': today + timedelta(days=2),
                'time': time(17, 0),
                'duration_minutes': 60,
                'price': 350.00,
                'status': 'scheduled',
                'description': 'Симуляція реального усного інтерв\'ю IELTS з персональним фідбеком.'
            }
        )
        lesson2, _ = Lesson.objects.get_or_create(
            teacher=teacher1,
            title='IELTS Writing Task 2: Opinion Essays',
            defaults={
                'course': course1,
                'lesson_type': 'Individual',
                'english_level': 'C1',
                'date': today + timedelta(days=3),
                'time': time(15, 0),
                'duration_minutes': 60,
                'price': 450.00,
                'status': 'scheduled',
                'description': 'Аналіз есе з оцінкою на 8.0, структура аргументів та когезія.'
            }
        )
        lesson3, _ = Lesson.objects.get_or_create(
            teacher=teacher2,
            title='Tech Demo Presentation & Q&A Pitch',
            defaults={
                'course': course2,
                'lesson_type': 'Business English',
                'english_level': 'B2',
                'date': today + timedelta(days=4),
                'time': time(19, 0),
                'duration_minutes': 90,
                'price': 600.00,
                'status': 'scheduled',
                'description': 'Практикуємо захист проєкту перед стейкхолдерами та відповіді на складні запитання.'
            }
        )
        lesson4, _ = Lesson.objects.get_or_create(
            teacher=teacher3,
            title='Friday Night Speaking Club: AI Trends',
            defaults={
                'course': course3,
                'lesson_type': 'Speaking Club',
                'english_level': 'B1',
                'date': today + timedelta(days=5),
                'time': time(18, 30),
                'duration_minutes': 60,
                'price': 250.00,
                'status': 'scheduled',
                'description': 'Обговорюємо штучний інтелект та майбутнє професій у дружній атмосфері.'
            }
        )

        # 6. Sample Booking for student
        Booking.objects.get_or_create(
            user=student_user,
            teacher=teacher1,
            date=today + timedelta(days=2),
            time=time(17, 0),
            defaults={
                'lesson': lesson1,
                'lesson_type': 'Speaking Club',
                'status': 'confirmed',
                'notes': 'Хочу звернути особливу увагу на вимову та флуентність.'
            }
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
        self.stdout.write("Created accounts:")
        self.stdout.write(" - Admin: username 'admin', password 'Admin1234!'")
        self.stdout.write(" - Student: username 'student', password 'Student1234!'")
