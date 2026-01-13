import re

from app.core.exceptions.validation import ValidationError


def validate_password(password: str) -> None:
    if not password:
        raise ValidationError("password_required")
    if " " in password:
        raise ValidationError("password_cannot_contain_spaces")
    if len(password) < 8:
        raise ValidationError("password_too_short")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("password_needs_uppercase")
    if not re.search(r"[a-z]", password):
        raise ValidationError("password_needs_lowercase")
    if not re.search(r"[0-9]", password):
        raise ValidationError("password_needs_number")
