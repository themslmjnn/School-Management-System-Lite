from pydantic import BaseModel, Field

from typing import Optional
from datetime import date

from src.models.student_model import StudentStatus
from src.schemas.user_schemas import UserCreateAdmin, UserResponseAdmin, UserResponsePublic, UserSearchPublic, UserSearchAdmin
from src.schemas.base_schema import BaseSchema


class StudentBase(BaseModel):
    grade: str
    enrolled_at: date
    status: StudentStatus



class StudentCreateAdmin(BaseModel):
    user: UserCreateAdmin
    student: StudentBase


class StudentResponseBase(StudentBase, BaseSchema):
    id: int


class StudentResponsePublic(BaseModel, BaseSchema):
    user: UserResponsePublic
    student: StudentBase


class StudentResponseAdmin(BaseModel, BaseSchema):
    user: UserResponseAdmin
    student: StudentResponseBase


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


class StudentSubjectResponseAdmin(StudentSubjectBase, BaseSchema):
    id: int


class StudentSubjectUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None


class StudentGroupBase(BaseModel):
    student_id: int = Field(ge=1)
    group_id: int = Field(ge=1)


class StudentGroupCreateAdmin(StudentGroupBase):
    pass


class StudentGroupResponseAdmin(StudentGroupBase, BaseSchema):
    id: int


class StudentGroupUpdateInfoAdmin(BaseModel):
    student_id: Optional[int] = None
    group_id: Optional[int] = None