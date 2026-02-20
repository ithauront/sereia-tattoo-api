import re

from app.core.exceptions.validation import ValidationError

BRAZIL_PHONE_REGEX = re.compile(r"^\d+$")
VALID_DDDs = {
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "21",
    "22",
    "24",
    "27",
    "28",
    "31",
    "32",
    "33",
    "34",
    "35",
    "37",
    "38",
    "41",
    "42",
    "43",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "51",
    "53",
    "54",
    "55",
    "61",
    "62",
    "63",
    "64",
    "65",
    "66",
    "67",
    "68",
    "69",
    "71",
    "73",
    "74",
    "75",
    "77",
    "79",
    "81",
    "82",
    "83",
    "84",
    "85",
    "86",
    "87",
    "88",
    "89",
    "91",
    "92",
    "93",
    "94",
    "95",
    "96",
    "97",
    "98",
    "99",
}


def validate_phone_number(phone: str) -> None:
    if not phone:
        raise ValidationError("phone_required")

    if not BRAZIL_PHONE_REGEX.match(phone):
        raise ValidationError("phone_must_contain_only_numbers")

    if len(phone) not in (10, 11):
        raise ValidationError("phone_must_have_10_or_11_digits")

    ddd = phone[:2]
    if ddd not in VALID_DDDs:
        raise ValidationError("phone_invalid_ddd")

    if len(phone) == 11 and phone[2] != "9":
        raise ValidationError("mobile_phone_must_start_with_9")
