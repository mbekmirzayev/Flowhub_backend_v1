from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class CheckSessionMiddleware(MiddlewareMixin):
    def process_resource(self, request):

        from apps.device.models.session import UserSession

        if request.user.is_authenticated and request.auth:
            token_device_id = request.auth.get('device_id')

            if token_device_id:
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
        return None
