import re

from app.core.exceptions.validation import ValidationError

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]+$")


def validate_username(username: str) -> None:
    if not username:
        raise ValidationError("username_required")
    if " " in username:
        raise ValidationError("username_cannot_contain_spaces")
    if len(username) < 3 or len(username) > 30:
        raise ValidationError("username_must_have_between_3_and_30_characters")
    if not any(char.isalpha() for char in username):
        raise ValidationError("username_must_contain_letters")
    if not USERNAME_REGEX.match(username):
        raise ValidationError("username_invalid_characters")
