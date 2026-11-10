from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom exception handler to ensure a consistent JSON error format
    across all API endpoints:
    {
        "error": "Message describing error",
        "details": ... (optional),
        "status_code": 4xx/5xx
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        status_code = response.status_code

        if isinstance(data, dict):
            # Check for standard 'detail'
            if 'detail' in data:
                detail_msg = str(data['detail'])
                # Translate common DRF messages to clear Ukrainian text if helpful
                if "Authentication credentials were not provided" in detail_msg:
                    error_msg = "Автентифікаційні дані не надано."
                elif "Given token not valid" in detail_msg or "token_not_valid" in detail_msg:
                    error_msg = "Токен недійсний або прострочений."
                elif "You do not have permission" in detail_msg:
                    error_msg = "У вас немає прав для виконання цієї дії."
                elif "Not found" in detail_msg:
                    error_msg = "Запитуваний ресурс не знайдено."
                else:
                    error_msg = detail_msg

                response.data = {
                    "error": error_msg,
                    "details": detail_msg,
                    "status_code": status_code
                }
            else:
                response.data = {
                    "error": "Помилка валідації даних.",
                    "details": data,
                    "status_code": status_code
                }
        elif isinstance(data, list):
            response.data = {
                "error": str(data[0]) if len(data) > 0 else "Помилка обробки запиту.",
                "details": data,
                "status_code": status_code
            }
        else:
            response.data = {
                "error": str(data),
                "status_code": status_code
            }

    return response

