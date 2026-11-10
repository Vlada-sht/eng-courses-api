from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    RefreshTokenAPIView,
    LogoutAPIView,
    CurrentUserAPIView,
    CurrentUserBookingsAPIView,
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='user-register'),
    path('register', RegisterAPIView.as_view()),
    path('login/', LoginAPIView.as_view(), name='user-login'),
    path('login', LoginAPIView.as_view()),
    path('logout/', LogoutAPIView.as_view(), name='user-logout'),
    path('logout', LogoutAPIView.as_view()),
    path('refresh/', RefreshTokenAPIView.as_view(), name='user-refresh'),
    path('token/refresh/', RefreshTokenAPIView.as_view(), name='user-token-refresh'),
    path('me/', CurrentUserAPIView.as_view(), name='user-me'),
    path('me/bookings/', CurrentUserBookingsAPIView.as_view(), name='user-me-bookings'),
    path('me/bookings', CurrentUserBookingsAPIView.as_view()),
]
