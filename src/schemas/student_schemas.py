from pydantic import BaseModel, ConfigDict

from typing import Optional
from datetime import date

from src.models.student_model import StudentStatus
from src.schemas.user_schemas import UserCreateAdmin, UserResponseAdmin, UserResponseGeneral, UserSearchGeneral, UserSearchAdmin

# Done
class StudentBase(BaseModel):
    grade: str
    enrolled_at: date
    status: StudentStatus


# Done
class StudentCreateAdmin(BaseModel):
    user_data: UserCreateAdmin
    student_advanced_data: StudentBase


# Done
class StudentResponseBase(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Done
class StudentResponseGeneral(BaseModel):
    user_data: UserResponseGeneral
    student_advanced_data: StudentBase

    model_config = ConfigDict(from_attributes=True)


# Done
class StudentResponseAdmin(BaseModel):
    user_data: UserResponseAdmin
    student_advanced_data: StudentResponseBase

    model_config = ConfigDict(from_attributes=True)



class StudentUpdateInfoAdmin(BaseModel):
    grade: Optional[str] = None
    enrolled_at: Optional[date] = None  
    status: Optional[StudentStatus] = None


class StudentSearchBase(BaseModel):
    grade: str


class StudentSearchGeneral(StudentSearchBase, UserSearchGeneral):
    pass


class StudentSearchAdmin(StudentSearchBase, UserSearchAdmin):
    pass