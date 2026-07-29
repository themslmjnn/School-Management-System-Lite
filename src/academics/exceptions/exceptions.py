from src.utils.base_exception import AppException


class TeachingAssignmentAlreadyExistsError(AppException):
    status_code = 409


class HeadOfClassSlotAlreadyFilledError(AppException):
    status_code = 409


class TeacherAlreadyHeadOfClassForGroupError(AppException):
    status_code = 409


class StudentAlreadyEnrolledError(AppException):
    status_code = 409


class StudentNotInGroupError(AppException):
    status_code = 409


class StudentNotFoundError(AppException):
    status_code = 404


class StudentSubjectEnrollmentNotFoundError(AppException):
    status_code = 404
