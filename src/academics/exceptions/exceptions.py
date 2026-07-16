from src.utils.base_exception import AppException


class TeachingAssignmentAlreadyExistsError(AppException):
    pass


class HeadOfClassSlotAlreadyFilledError(AppException):
    pass


class TeacherAlreadyHeadOfClassForGroupError(AppException):
    pass


class StudentAlreadyEnrolledError(AppException):
    pass


class StudentNotInGroupError(AppException):
    pass


class StudentNotFoundError(AppException):
    pass


class StudentSubjectEnrollmentNotFoundError(AppException):
    pass
