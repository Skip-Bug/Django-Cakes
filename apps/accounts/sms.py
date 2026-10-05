import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

SMSRU_SEND_URL = "https://sms.ru/sms/send"


def _normalize_for_smsru(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def _log_otp(phone: str, code: str, reason: str) -> None:
    if settings.OTP_LOG_TO_CONSOLE:
        logger.warning("[OTP:%s] %s -> %s", reason, phone, code)


def send_otp(phone: str, code: str) -> bool:
    if settings.OTP_DEMO_MODE:
        _log_otp(phone, code, "demo-mode")
        return True

    api_id = settings.SMSRU_API_ID

    if not api_id:
        _log_otp(phone, code, "fallback-no-api-id")
        return False

    params = {
        "api_id": api_id,
        "to": _normalize_for_smsru(phone),
        "msg": f"Код подтверждения: {code}",
        "json": 1,
    }
    if settings.SMSRU_FROM:
        params["from"] = settings.SMSRU_FROM

    url = f"{SMSRU_SEND_URL}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=settings.SMSRU_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
    except Exception:
        logger.exception("SMS.ru: сеть/таймаут при отправке на %s", phone)
        _log_otp(phone, code, "network-error")
        return False

    try:
        data = json.loads(body)
    except ValueError:
        logger.error("SMS.ru: невалидный JSON: %s", body[:200])
        _log_otp(phone, code, "bad-json")
        return False

    if data.get("status") != "OK":
        logger.error(
            "SMS.ru: ошибка верхнего уровня %s — %s",
            data.get("status_code"),
            data.get("status_text"),
        )
        _log_otp(phone, code, "smsru-top-error")
        return False

    sms_info = (data.get("sms") or {}).get(params["to"]) or {}
    if sms_info.get("status") != "OK":
        logger.error(
            "SMS.ru: номер %s не принят: %s (%s)",
            phone,
            sms_info.get("status_code"),
            sms_info.get("status_text"),
        )
        _log_otp(phone, code, "smsru-rejected")
        return False

    logger.info(
        "SMS.ru: код для %s отправлен (sms_id=%s)",
        phone,
        sms_info.get("sms_id"),
    )

    _log_otp(phone, code, "sent-ok")
    return True
