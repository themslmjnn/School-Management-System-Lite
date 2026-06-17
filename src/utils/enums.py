from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    director = "director"
    vice_director = "vice_director"
    teacher = "teacher"
    student = "student"
    parent = "parent"
