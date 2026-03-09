from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
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


class TeacherSubjectBase(BaseModel):
    teacher_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class TeacherSubjectCreateAdmin(TeacherSubjectBase):
    pass


class TeacherSubjectResponseAdmin(TeacherSubjectBase):
    id: int


    model_config = ConfigDict(from_attributes=True)


class TeacherSubjectUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    subject_id: Optional[int] = None


class TeacherGroupBase(BaseModel):
    student_id: int = Field(ge=1)
    subject_id: int = Field(ge=1)


class TeacherGroupCreateAdmin(TeacherSubjectBase):
    pass


class TeacherGroupResponseAdmin(TeacherSubjectBase):
    id: int


    model_config = ConfigDict(from_attributes=True)


class TeacherGroupUpdateInfoAdmin(BaseModel):
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None