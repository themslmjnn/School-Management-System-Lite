from sqlalchemy.ext.asyncio import AsyncSession

from src.core.pagination import PaginatedResponse
from src.guardian_links.repository import GuardianLinkRepository
from src.guardian_links.schemas import GuardianLinkResponse
from src.guardian_links.utils.constants import HTTP404
from src.guardian_links.utils.exceptions import GuardianLinkNotFoundError
from src.guardian_links.utils.helpers import build_guardian_link_response
from src.utils.helpers import ensure_exists


class GuardianLinkServiceDirector:
    @staticmethod
    async def get_links(
        session: AsyncSession,
        skip: int,
        limit: int,
    ) -> PaginatedResponse:
        links, total = await GuardianLinkRepository.get_links(session, skip, limit)

        return PaginatedResponse(
            items=[build_guardian_link_response(link) for link in links],
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total,
        )

    @staticmethod
    async def get_link_by_id(
        session: AsyncSession,
        link_id: int,
    ) -> GuardianLinkResponse:
        link = await GuardianLinkRepository.get_link_by_id(session, link_id)
        ensure_exists(link, GuardianLinkNotFoundError(HTTP404.GUARDIAN_LINK))

        return build_guardian_link_response(link)
