from sqlalchemy.ext.asyncio import AsyncSession

from src.guardian_links.repository import GuardianLinkRepository
from src.guardian_links.schemas import GuardianLinkResponse
from src.guardian_links.utils.constants import HTTP404
from src.guardian_links.utils.exceptions import GuardianLinkNotFoundError
from src.guardian_links.utils.helpers import build_guardian_link_response
from src.utils.helpers import ensure_exists


class GuardianLinkServiceHeadOfClass:
    @staticmethod
    async def get_my_student_links(
        session: AsyncSession,
        teacher_id: int,
    ) -> list[GuardianLinkResponse]:
        links = await GuardianLinkRepository.get_links_for_head_of_class(
            session, teacher_id
        )

        return [build_guardian_link_response(link) for link in links]

    @staticmethod
    async def get_my_student_link_by_id(
        session: AsyncSession,
        teacher_id: int,
        link_id: int,
    ) -> GuardianLinkResponse:
        link = await GuardianLinkRepository.get_link_for_head_of_class_by_id(
            session, teacher_id, link_id
        )
        ensure_exists(link, GuardianLinkNotFoundError(HTTP404.GUARDIAN_LINK))

        return build_guardian_link_response(link)
