from sqlalchemy.exc import IntegrityError

from src.utils.base_exception import AppException


class InvalidGuardianLinkError(AppException):
    status_code = 400


class GuardianLinkAlreadyExistsError(AppException):
    status_code = 409


class GuardianSlotAlreadyFilledError(AppException):
    status_code = 409


class GuardianLinkNotFoundError(AppException):
    status_code = 404


def handle_guardian_student_pair_error(error: IntegrityError) -> None:
    if "uix_guardian_student_pair" in str(error.orig):
        raise GuardianLinkAlreadyExistsError("This guardian link could not be created")


def handle_one_primary_guardian_per_student_error(error: IntegrityError) -> None:
    if "uix_one_primary_guardian_per_student" in str(error.orig):
        raise GuardianSlotAlreadyFilledError(
            "Guardian with this priority already exists"
        )


def handle_one_secondary_guardian_per_student_error(error: IntegrityError) -> None:
    if "uix_one_secondary_guardian_per_student" in str(error.orig):
        raise GuardianSlotAlreadyFilledError(
            "Guardian with this priority already exists"
        )
