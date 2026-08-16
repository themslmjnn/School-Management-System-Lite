from src.guardian_links.models import StudentGuardianLink

from src.guardian_links.schemas import GuardianLinkResponse, GuardianLinkResponseAdmin


def _fullname(user) -> str:
    parts = [user.firstname, user.middlename, user.lastname]

    return " ".join(p for p in parts if p)


def build_guardian_link_response(link: StudentGuardianLink) -> GuardianLinkResponse:
    return GuardianLinkResponse(
        id=link.id,
        guardian_fullname=_fullname(link.guardian),
        student_fullname=_fullname(link.student),
        student_grade_level=link.student.group.grade_level
        if link.student.group
        else None,
        priority=link.priority,
    )


def build_guardian_link_response_admin(
    link: StudentGuardianLink,
) -> GuardianLinkResponseAdmin:
    return GuardianLinkResponseAdmin(
        id=link.id,
        guardian_id=link.guardian_id,
        student_id=link.student_id,
        guardian_fullname=_fullname(link.guardian),
        student_fullname=_fullname(link.student),
        student_grade_level=link.student.group.grade_level
        if link.student.group
        else None,
        priority=link.priority,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )
