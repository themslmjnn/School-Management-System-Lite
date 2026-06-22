import re
from datetime import date

from pydantic_core import PydanticCustomError


def validate_username(username: str) -> str:
    if any(symbol in "\\~`!@#$%^&*()-=+{}[]|;:'<>,/?\"" for symbol in username):
        raise PydanticCustomError(
            "invalid_username_symbols",
            "Username can only contain (.) and (_) symbols",
        )

    if not username.replace(".", "").replace("_", "").isalnum():
        raise PydanticCustomError(
            "invalid_username_characters",
            "Username can only contain lowercase letters and numbers",
        )

    return username


def validate_firstname(firstname: str) -> str:
    if not firstname.isalpha():
        raise PydanticCustomError(
            "invalid_firstname_characters",
            "First name can only contain letters",
        )

    return firstname


def validate_lastname(lastname: str) -> str:
    if not lastname.isalpha():
        raise PydanticCustomError(
            "invalid_firstname_characters",
            "Last name can only contain letters",
        )

    return lastname


def validate_middlename(middlename: str) -> str:
    if not middlename.isalpha():
        raise PydanticCustomError(
            "invalid_middlename_characters",
            "Middle name can only contain letters",
        )

    return middlename


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


def validate_phone_number(phone_number: str) -> str:
    phone_number = phone_number.strip()

    normalized = re.sub(r"[\s\-().]", "", phone_number)

    if normalized.startswith("+"):
        digits = normalized[1:]
    elif normalized.startswith("00"):
        digits = normalized[2:]
    else:
        raise PydanticCustomError(
            "phone_number_invalid_format",
            "Phone number must start with '+' or '00' country code",
        )

    if not digits.isdigit():
        raise PydanticCustomError(
            "phone_number_invalid_format",
            "Phone number contains invalid characters",
        )

    if len(digits) < 7:
        raise PydanticCustomError(
            "phone_number_too_short",
            "Phone number must contain at least 7 digits",
        )

    if len(digits) > 15:
        raise PydanticCustomError(
            "phone_number_too_long",
            "Phone number must not exceed 15 digits",
        )

    return phone_number
