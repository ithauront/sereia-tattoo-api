from app.core.exceptions.validation import ValidationError


def validate_text(text: str, *, min_length: int = 5) -> str:
    """Validate free text and return it without surrounding whitespace."""

    normalized_text = text.strip()

    if not normalized_text:
        raise ValidationError("text_required")
    if len(normalized_text) < min_length:
        raise ValidationError(f"text_must_have_at_least_{min_length}_characters")
    if not any(char.isalpha() for char in normalized_text):
        raise ValidationError("text_must_contain_letters")

    return normalized_text
