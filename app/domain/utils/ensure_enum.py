from app.core.exceptions.validation import ValidationError


def ensure_enum(value, enum_cls):
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        raise ValidationError(f"Invalid value '{value}' for {enum_cls.__name__}")
