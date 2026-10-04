import phonenumbers


def normalize_phone(raw, region="RU"):
    """Приводит номер к E164. Возвращает None, если номер невалиден."""
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
