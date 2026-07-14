import re
from datetime import date

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberType
from pydantic_core import PydanticCustomError


def validate_username(username: str) -> str:
    if not re.fullmatch(r"[a-z0-9._]+", username):
        raise PydanticCustomError(
            "invalid_username_characters",
            "Username can only contain lowercase letters, numbers, (.) and (_)",
        )

    if not username[0].isalpha():
        raise PydanticCustomError(
            "invalid_username_start",
            "Username must start with a letter",
        )

    if username[-1] in (".", "_"):
        raise PydanticCustomError(
            "invalid_username_end",
            "Username cannot end with (.) or (_)",
        )

    if re.search(r"[._]{2}", username):
        raise PydanticCustomError(
            "invalid_username_consecutive",
            "Username cannot contain consecutive (.) or (_) characters",
        )

    return username


def validate_firstname(firstname: str) -> str:
    if not firstname.isalpha():
        raise PydanticCustomError(
            "invalid_firstname_characters",
            "First name can only contain letters",
        )

    return firstname.capitalize()


def validate_lastname(lastname: str) -> str:
    if not lastname.isalpha():
        raise PydanticCustomError(
            "invalid_firstname_characters",
            "Last name can only contain letters",
        )

    return lastname.capitalize()


def validate_middlename(middlename: str) -> str:
    if not middlename.isalpha():
        raise PydanticCustomError(
            "invalid_middlename_characters",
            "Middle name can only contain letters",
        )

    return middlename.capitalize()


def validate_date_of_birth(birth_date: date) -> date:
    today = date.today()

    if birth_date >= today:
        raise PydanticCustomError(
            "date_of_birth_not_in_past",
            "Date of birth must be in the past",
        )

    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )

    if age < 6:
        raise PydanticCustomError(
            "date_of_birth_too_young",
            "User must be at least 6 years old",
        )
    if age > 21:
        raise PydanticCustomError(
            "date_of_birth_invalid",
            "Please enter a valid date of birth",
        )

    return birth_date


def validate_password(password: str) -> str:
    if not any(c.isupper() for c in password):
        raise PydanticCustomError(
            "password_no_uppercase",
            "Password must contain at least one uppercase letter",
        )

    if not any(c.isdigit() for c in password):
        raise PydanticCustomError(
            "password_no_digit",
            "Password must contain at least one digit",
        )

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        raise PydanticCustomError(
            "password_no_special_character",
            "Password must contain at least one special character",
        )

    return password


def parse_and_validate_mobile_number(phone_number: str) -> str:
    phone_number = phone_number.strip()

    try:
        parsed = phonenumbers.parse(phone_number, None)
    except NumberParseException as err:
        raise PydanticCustomError(
            "phone_number_invalid_format",
            "Phone number must be in international format, e.g. +14155552671",
        ) from err

    if not phonenumbers.is_valid_number(parsed):
        raise PydanticCustomError(
            "phone_number_invalid",
            "Phone number is not a valid number for its country",
        )

    number_type = phonenumbers.number_type(parsed)
    if number_type not in (
        PhoneNumberType.MOBILE,
        PhoneNumberType.FIXED_LINE_OR_MOBILE,
    ):
        raise PydanticCustomError(
            "phone_number_not_mobile",
            "Phone number must be a mobile number",
        )

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def format_phone_for_display(canonical_digits: str) -> str:
    parsed = phonenumbers.parse("+" + canonical_digits, None)

    return phonenumbers.format_number(
        parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )
