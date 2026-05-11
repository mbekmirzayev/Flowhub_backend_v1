import random

from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from api.utils.phone.normalize_phone import normalize_phone

OTP_KEY_PREFIX = "otp"
LIMIT_KEY_PREFIX = "limit"
TEMP_USER_PREFIX = "temp_user"


def get_otp_key(phone: str) -> str:
    return f"{OTP_KEY_PREFIX}:{phone}"


def get_limit_key(phone: str) -> str:
    return f"{LIMIT_KEY_PREFIX}:{phone}"


def get_temp_user_key(phone: str) -> str:
    return f"{TEMP_USER_PREFIX}:{phone}"


def send_verification_code(phone: str):
    phone = normalize_phone(phone)
    limit_key = get_limit_key(phone)
    code_key = get_otp_key(phone)  # "otp:+998..."

    remaining = cache.ttl(limit_key)
    if remaining and remaining > 0:
        raise ValidationError({
            "message": f"Iltimos, {remaining} soniyadan keyin qayta urinib ko'ring"
        })

    code = str(random.randint(100000, 999999))
    print(f"[DEBUG] OTP | phone={phone} | code={code} | key={code_key}")

    cache.set(code_key, code, timeout=300)  # 5 daqiqa
    cache.set(limit_key, True, timeout=60)  # 1 daqiqa rate-limit

    # send_sms(phone, code)  ← SMS xizmati
    return code


def check_verification_code(phone: str, code: str) -> bool:
    cached = cache.get(get_otp_key(phone))
    print(f"[DEBUG] CHECK | key={get_otp_key(phone)} | cached={cached} | input={code}")
    return cached is not None and str(cached) == str(code)
