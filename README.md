English Courses API

Опис проєкту

Це REST API для онлайн-платформи вивчення англійської мови. Сервіс дозволяє студентам знаходити репетиторів з англійської за рівнем володіння мовою (від A1 до C2) та напрямком (Speaking Club, Business English, підготовка до IELTS/TOEFL), бронювати онлайн-заняття на зручний час та переглядати історію своїх уроків в особистому кабінеті.

Архітектура REST API

Усі дані передаються та повертаються у форматі JSON. Нижче наведено опис основних ендпоінтів для клієнтської частини.

1. Користувачі (Users)

Реєстрація нового користувача

Використання: Створення акаунту для нового студента.

Method: POST

Endpoint: /api/users/register

Request body:

{
  "name": "Владислава",
  "email": "vlada@gmail.com",
  "password": "password123",
  "english_level": "B2"
}


Response status: 201 Created

Response body:

{
  "id": 1,
  "name": "Владислава",
  "email": "vlada@gmail.com"
}


Авторизація користувача

Використання: Вхід у систему.

Method: POST

Endpoint: /api/users/login

Request body:

{
  "email": "vlada@gmail.com",
  "password": "password123"
}


Response status: 200 OK

Response body:

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5c..."
}


2. Викладачі (Teachers)

Отримання списку викладачів англійської

Використання: Перегляд всіх репетиторів з можливістю фільтрації за напрямком або рівнем.

Method: GET

Endpoint: /api/teachers

Parameters: ?specialization=IELTS або ?level=B2 (опціонально)

Response status: 200 OK

Response body:

[
  {
    "id": 101,
    "name": "Lily Snape",
    "specialization": "IELTS Prep",
    "price_per_hour": 450,
    "rating": 4.95
  }
]


Детальна інформація про викладача

Використання: Перегляд профілю конкретного викладача (досвід, ціна за годину).

Method: GET

Endpoint: /api/teachers/{id}

Response status: 200 OK

Response body:

{
  "id": 101,
  "name": "Lily Snape",
  "bio": "CELTA certified tutor with 5 years of experience",
  "price_per_hour": 450
}


3. Заняття та Бронювання (Lessons & Bookings)

Запис на урок

Використання: Студент обирає дату та час і бронює урок у репетитора.

Method: POST

Endpoint: /api/bookings

Request body:

{
  "teacher_id": 101,
  "date": "2026-10-25",
  "time": "16:00",
  "lesson_type": "Speaking Club"
}


Response status: 201 Created

Response body:

{
  "booking_id": 12,
  "status": "confirmed",
  "message": "Заняття успішно заброньовано"
}


Перегляд моїх занять

Використання: Студент бачить свої заплановані та пройдені уроки.

Method: GET

Endpoint: /api/users/me/bookings

Response status: 200 OK

Response body:

[
  {
    "booking_id": 12,
    "teacher_name": "Lily Snape",
    "date": "2026-10-25",
    "time": "16:00",
    "status": "confirmed"
  }
]


}




(TODO: доробити ендпоінти для скасування бронювання та оцінювання викладача)

Схема бази даних


(Схема створюється в draw.io і додається у репозиторій під назвою db_schema.png)
