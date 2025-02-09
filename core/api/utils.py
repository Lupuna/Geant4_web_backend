from rest_framework import status
from rest_framework.response import Response


def response_cookies(response_data, status, cookies_data=None, delete=False):
    response = Response(response_data, status)
# не забыть поставить secure=True когда будет https
    if cookies_data:

        if not delete:
            for key in cookies_data:
                response.set_cookie(
                    key=key, value=cookies_data[key], httponly=True, secure=False, samesite='Lax')
        else:
            for key in cookies_data:
                response.delete_cookie(key=key)

    return response
