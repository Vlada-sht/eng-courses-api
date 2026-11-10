from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserSerializer, UserUpdateSerializer
from courses.models import Booking

def error_response(message, status_code, details=None):
    payload = {"error": message, "status_code": status_code}
    if details is not None:
        payload["details"] = details
    return Response(payload, status=status_code)


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Помилка валідації при реєстрації користувача.",
                status.HTTP_400_BAD_REQUEST,
                details=serializer.errors
            )

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Користувача успішно зареєстровано.",
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        identifier = data.get('username') or data.get('email')
        password = data.get('password')

        if not identifier or not password:
            return error_response(
                "Логін/email та пароль є обов'язковими для заповнення.",
                status.HTTP_400_BAD_REQUEST,
                details={"fields": ["username/email", "password"]}
            )

        # Authenticate with username or email
        user = None
        if '@' in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                if user_obj.check_password(password):
                    user = user_obj
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=identifier, password=password)

        if user is None:
            return error_response(
                "Невірне ім'я користувача (email) або пароль.",
                status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return error_response(
                "Обліковий запис деактивовано.",
                status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "message": "Вхід успішно виконано.",
            "access": access_token,
            "refresh": str(refresh),
            "token": access_token,
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class RefreshTokenAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return error_response(
                "Поле 'refresh' є обов'язковим для оновлення токена.",
                status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            # If token rotation is enabled in SIMPLE_JWT, simplejwt can rotate
            response_data = {
                "access": new_access_token,
            }
            # Add rotated refresh if configured
            try:
                token.set_jti()
                token.set_exp()
                response_data["refresh"] = str(token)
            except Exception:
                response_data["refresh"] = refresh_token

            return Response(response_data, status=status.HTTP_200_OK)
        except (TokenError, InvalidToken) as e:
            return error_response(
                "Недійсний або прострочений refresh токен.",
                status.HTTP_401_UNAUTHORIZED,
                details=str(e)
            )


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken, AttributeError):
                pass

        return Response({
            "message": "Успішний вихід із системи. Токени видалено.",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Профіль успішно оновлено.",
                "user": UserSerializer(request.user).data
            }, status=status.HTTP_200_OK)
        return error_response(
            "Помилка оновлення профілю.",
            status.HTTP_400_BAD_REQUEST,
            details=serializer.errors
        )

    def patch(self, request):
        return self.put(request)


class CurrentUserBookingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).select_related('teacher', 'lesson').order_by('-date', '-time')
        data = []
        for b in bookings:
            data.append({
                "booking_id": b.id,
                "id": b.id,
                "teacher_id": b.teacher.id,
                "teacher_name": b.teacher.name,
                "date": str(b.date),
                "time": str(b.time),
                "lesson_type": b.lesson_type,
                "status": b.status,
                "notes": b.notes,
                "created_at": b.created_at.isoformat() if b.created_at else None
            })
        return Response(data, status=status.HTTP_200_OK)

