import re
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    english_level = serializers.CharField(source='profile.english_level', read_only=True)
    role = serializers.CharField(source='profile.role', read_only=True)
    phone = serializers.CharField(source='profile.phone', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'english_level', 'role', 'phone', 'is_staff', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
        error_messages={
            'required': "Пароль є обов'язковим полем.",
            'min_length': "Пароль має містити щонайменше 8 символів.",
            'max_length': "Пароль не може перевищувати 128 символів."
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
        error_messages={
            'required': "Повторне введення пароля (password confirmation) є обов'язковим."
        }
    )
    username = serializers.CharField(
        required=True,
        max_length=150,
        error_messages={
            'required': "Ім'я користувача (username) є обов'язковим.",
            'max_length': "Ім'я користувача не може перевищувати 150 символів."
        }
    )
    email = serializers.EmailField(
        required=True,
        max_length=254,
        error_messages={
            'required': "Електронна пошта (email) є обов'язковим полем.",
            'invalid': "Введіть коректну адресу електронної пошти (наприклад, name@example.com).",
            'max_length': "Email не може перевищувати 254 символи."
        }
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
        error_messages={'max_length': "Ім'я не може перевищувати 150 символів."}
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
        error_messages={'max_length': "Прізвище не може перевищувати 150 символів."}
    )
    english_level = serializers.ChoiceField(
        choices=UserProfile.LEVEL_CHOICES,
        default='B2',
        required=False
    )
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        default='student',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'english_level', 'role'
        ]

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Ім'я користувача не може бути порожнім.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Користувач з таким іменем користувача вже зареєстрований.")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
            raise serializers.ValidationError("Username може містити лише латинські літери, цифри та знаки _ . -")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Користувач з такою електронною поштою вже зареєстрований.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Паролі не збігаються."
            })

        # Password complexity: must contain letters and numbers
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            raise serializers.ValidationError({
                "password": "Пароль повинен містити як мінімум одну літеру та одну цифру."
            })

        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        english_level = validated_data.pop('english_level', 'B2')
        role = validated_data.pop('role', 'student')

        # Create user with properly hashed password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.english_level = english_level
        profile.role = role
        profile.save()

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    english_level = serializers.ChoiceField(choices=UserProfile.LEVEL_CHOICES, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'english_level']

    def update(self, instance, validated_data):
        english_level = validated_data.pop('english_level', None)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        if english_level:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            profile.english_level = english_level
            profile.save()

        return instance

