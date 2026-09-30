import random
from datetime import timedelta

import phonenumbers
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import PhoneOTP

User = get_user_model()


def normalize_phone(raw, region="RU"):
    try:
        parsed = phonenumbers.parse(raw or "", region)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    if phonenumbers.region_code_for_number(parsed) != region:
        return None
    return phonenumbers.format_number(
        parsed,
        phonenumbers.PhoneNumberFormat.E164,
    )


@require_POST
def request_code(request):
    phone = normalize_phone(request.POST.get("phone"))
    if not phone:
        return JsonResponse(
            {"ok": False, "error": "Некорректный номер телефона"},
            status=400,
        )

    last = (
        PhoneOTP.objects.filter(phone=phone)
        .order_by("-created_at")
        .first()
    )
    if last and (timezone.now() - last.created_at).total_seconds() < 60:
        return JsonResponse(
            {"ok": False, "error": "Код уже отправлен, подождите минуту"},
            status=429,
        )

    code = f"{random.randint(0, 999999):06d}"
    PhoneOTP.objects.create(
        phone=phone,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    # TODO: заменить на реального SMS-провайдера.
    if settings.DEBUG:
        print(f"[SMS] {phone}: {code}")

    return JsonResponse({"ok": True})


@require_POST
def verify_code(request):
    phone = normalize_phone(request.POST.get("phone"))
    code = (request.POST.get("code") or "").strip()

    if not phone or not code:
        return JsonResponse(
            {"ok": False, "error": "Нужен телефон и код"},
            status=400,
        )

    otp = (
        PhoneOTP.objects.filter(phone=phone, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp or not otp.is_valid():
        return JsonResponse(
            {"ok": False, "error": "Код истёк. Запросите новый"},
            status=400,
        )

    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    if otp.code != code:
        return JsonResponse({"ok": False, "error": "Неверный код"}, status=400)

    otp.is_used = True
    otp.save(update_fields=["is_used"])

    user, created = User.objects.get_or_create(username=phone)
    if created:
        user.set_unusable_password()
        user.save()

    login(request, user)

    return JsonResponse({"ok": True, "created": created})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"ok": True})


def check_auth(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"authenticated": False})
    return JsonResponse(
        {
            "authenticated": True,
            "phone": user.username,
        }
    )
