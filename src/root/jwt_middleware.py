import jwt
from django.conf import settings
from django.http import JsonResponse
from apps.device.models.session import UserSession


class CheckSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Header'dan Bearer tokenni qidiramiz
        auth_header = request.headers.get('Authorization', None)

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Tokenni decode qilamiz (SECRET_KEY orqali)
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'],
                                     options={"verify_signature": False})
                token_device_id = payload.get('device_id')

                # Agar foydalanuvchi tizimga kirgan bo'lsa va tokenda device_id bo'lsa
                if request.user and request.user.is_authenticated and token_device_id:
                    try:
                        session = UserSession.objects.get(
                            user=request.user,
                            device__device_id=token_device_id
                        )
                        session.save(update_fields=['last_used'])
                    except UserSession.DoesNotExist:
                        return JsonResponse({
                            'detail': 'Sessiya yaroqsiz yoki boshqa foydalanuvchi ushbu qurilmadan tizimga kirdi.',
                            'code': 'session_expired'
                        }, status=401)
            except Exception:
                # Token noto'g'ri bo'lsa buni DRF o'zi hal qiladi, middleware'da o'tkazib yuboramiz
                pass

        response = self.get_response(request)
        return response