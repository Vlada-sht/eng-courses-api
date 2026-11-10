from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Teacher(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)
    specialization = models.CharField(max_length=100, default='General English', blank=True)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=450.00)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.95)
    english_level = models.CharField(max_length=20, default='C2')
    experience_years = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.specialization}, {self.english_level})"


class Course(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    level = models.CharField(max_length=20, default='B2')
    english_level = models.CharField(max_length=20, default='B2')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='courses')
    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name='courses')
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.english_level and self.level:
            self.english_level = self.level
        elif not self.level and self.english_level:
            self.level = self.english_level
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='lessons')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    title = models.CharField(max_length=150)
    lesson_type = models.CharField(max_length=50, default='Speaking Club')
    english_level = models.CharField(max_length=20, default='B2')
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=350.00)
    status = models.CharField(max_length=20, default='scheduled')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.teacher.name} ({self.lesson_type}, {self.date} {self.time})"


class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='bookings')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    date = models.DateField()
    time = models.TimeField()
    lesson_type = models.CharField(max_length=50, default='Speaking Club')
    status = models.CharField(max_length=20, default='confirmed')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Booking #{self.id} for {self.user} with {self.teacher.name} on {self.date}"
