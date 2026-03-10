from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from datetime import date

from src.models.student_model import StudentStatus
from src.schemas.user_schemas import UserCreateAdmin, UserResponseAdmin, UserResponsePublic, UserSearchPublic, UserSearchAdmin

# Done
class StudentBase(BaseModel):
    grade: str
    enrolled_at: date
    status: StudentStatus


# Done
class StudentCreateAdmin(BaseModel):
    user: UserCreateAdmin
    student: StudentBase


# Done
class StudentResponseBase(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Done
class StudentResponsePublic(BaseModel):
    user: UserResponsePublic
    student: StudentBase

    model_config = ConfigDict(from_attributes=True)


# Done
class StudentResponseAdmin(BaseModel):
    user: UserResponseAdmin
    student: StudentResponseBase

    model_config = ConfigDict(from_attributes=True)



class StudentUpdateInfoAdmin(BaseModel):
    grade: Optional[str] = None
    enrolled_at: Optional[date] = None  
    status: Optional[StudentStatus] = None


class StudentSearchBase(StudentUpdateInfoAdmin):
    pass


class StudentSearchPublic(BaseModel):
    user: UserSearchPublic
    student: StudentSearchBase


class StudentSearchAdmin(BaseModel):
    user: UserSearchAdmin
    student: StudentSearchBase


class StudentSubjectBase(BaseModel):
    student_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class StudentSubjectCreateAdmin(StudentSubjectBase):
    pass


class StudentSubjectResponseAdmin(StudentSubjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class StudentSubjectUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None


class StudentGroupBase(BaseModel):
    student_id: int = Field(ge=1)
    group_id: int = Field(ge=1)


class StudentGroupCreateAdmin(StudentGroupBase):
    pass


class StudentGroupResponseAdmin(StudentGroupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class StudentGroupUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    group_id: Optional[int] = None