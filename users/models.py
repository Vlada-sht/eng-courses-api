from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )

    LEVEL_CHOICES = (
        ('A1', 'Beginner (A1)'),
        ('A2', 'Elementary (A2)'),
        ('B1', 'Intermediate (B1)'),
        ('B2', 'Upper-Intermediate (B2)'),
        ('C1', 'Advanced (C1)'),
        ('C2', 'Proficiency (C2)'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    english_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='B2')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role}, {self.english_level})"
