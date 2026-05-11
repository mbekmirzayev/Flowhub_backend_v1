from django.core.cache import cache
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.auth.serializers.verify_code import VerifyCodeSerializer
from api.users.serializers.profile import UserModelSerializer
from api.utils.otp.send_check_otp import get_otp_key, TEMP_USER_PREFIX, get_temp_user_key, check_verification_code
from api.utils.phone.normalize_phone import normalize_phone
from apps.users.models import User, TeacherProfile, StudentProfile, StaffProfile



@extend_schema(tags=["auth"])
class VerifyCodeAPI(APIView):
    serializer_class = VerifyCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = normalize_phone(serializer.validated_data['phone'])
        code = serializer.validated_data['code']

        # 1. SMS kodni tekshirish
        code_key = get_otp_key(phone)
        cached_code = cache.get(code_key)

        print(f"DEBUG: Key: {code_key}")
        print(f"DEBUG: Cached Code: {cached_code} (Type: {type(cached_code)})")
        print(f"DEBUG: Input Code: {code} (Type: {type(code)})")

        if not check_verification_code(phone, code):
            return Response({'error': "Kod noto'g'ri yoki muddati o'tgan"}, status=400)

        # 2. Keshdan vaqtinchalik ma'lumotlarni olish
        temp_key = get_temp_user_key(phone)
        user_data = cache.get(temp_key)

        if not user_data:
            return Response({"error": "Ro'yxatdan o'tish ma'lumotlari topilmadi"}, status=400)

        role = user_data.get('role')

        try:
            with transaction.atomic():
                # 3. Userni yaratish
                # create_user metodidan foydalanamiz (parol hash qilinishi uchun)
                user = User.objects.create_user(
                    phone=phone,
                    password=user_data.get('password'),  # Studentda bu None bo'ladi, create_user buni ko'taradi
                    first_name=user_data.get('first_name'),
                    last_name=user_data.get('last_name'),
                    organization_id=user_data.get('organization_id'),
                    role=role,
                    is_active=True,
                    is_staff=(role != User.Status.STUDENT)
                )

                # 4. Role bo'yicha Profil yaratish
                if role == User.Status.TEACHER:
                    TeacherProfile.objects.create(
                        user=user,
                        subject=user_data.get('subject', 'Noma\'lum'),
                        work_type=user_data.get('work_type', TeacherProfile.WorkType.FULL_TIME),
                    )

                elif role == User.Status.STUDENT:
                    StudentProfile.objects.create(
                        user=user,
                        parent_phone=user_data.get('parent_phone'),
                        status=StudentProfile.StudentStatus.ACTIVE,
                        # group_id modelingizda bo'lsa, uni ham qo'shishingiz mumkin
                    )

                elif role in [User.Status.MANAGER, User.Status.ADMIN]:
                    # StaffProfile modeli uchun
                    StaffProfile.objects.create(
                        user=user,
                        # Agar StaffProfile'da qo'shimcha fieldlar bo'lsa (masalan salary)
                        # user_data.get('salary') qilib yozish mumkin
                    )

            # 5. Muvaffaqiyatli bo'lsa keshni tozalaymiz
            cache.delete(temp_key)
            cache.delete(code_key)

            return Response({
                "message": "Foydalanuvchi muvaffaqiyatli tasdiqlandi va yaratildi.",
                "user": UserModelSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Xatolikni ko'rish (masalan, bazada fieldlar mos kelmasa)
            return Response({'error': f"Bazaga yozishda xatolik: {str(e)}"}, status=400)
