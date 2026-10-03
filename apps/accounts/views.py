import random
from datetime import timedelta

import phonenumbers
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse
from django.shortcuts import redirect
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
        return redirect("/?reg=code")

    last = PhoneOTP.objects.filter(phone=phone).order_by("-created_at").first()
    if last and (timezone.now() - last.created_at).total_seconds() < 60:
        return redirect("/?reg=error")

    code = f"{random.randint(0, 999999):06d}"
    PhoneOTP.objects.create(
        phone=phone,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    # TODO: заменить на реального SMS-провайдера.
    if settings.DEBUG:
        print(f"[SMS] {phone}: {code}")

    request.session["otp_phone"] = phone
    return redirect("/?reg=code")


@require_POST
def verify_code(request):
    phone = normalize_phone(
        request.POST.get("phone") or request.session.get("otp_phone")
    )
    code = (request.POST.get("code") or "").strip()

    if not phone or not code:
        return redirect("/?reg=error")

    otp = (
        PhoneOTP.objects.filter(phone=phone, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp or not otp.is_valid():
        return redirect("/?reg=error")

    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    if otp.code != code:
        return redirect("/?reg=error")

    otp.is_used = True
    otp.save(update_fields=["is_used"])

    user, created = User.objects.get_or_create(phone=phone)
    if created:
        user.set_unusable_password()
        user.save()

    login(request, user)

    return redirect("/lk/")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("/")


def check_auth(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"authenticated": False})
    return JsonResponse(
        {
            "authenticated": True,
            "phone": str(user.phone),
            "name": user.name,
            "email": user.email,
        }
    )


@require_POST
def update_profile(request):
    if not request.user.is_authenticated:
        return redirect("/")

    user = request.user
    user.name = request.POST.get("name", "").strip()
    user.email = request.POST.get("email", "").strip()
    user.address = request.POST.get("address", "").strip()
    user.save(update_fields=["name", "email", "address"])

    return redirect("/lk/")
