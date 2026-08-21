from sqlalchemy.ext.asyncio import AsyncSession

from src.emails.schemas import SearchEmailAdmin
from src.emails.service import PendingEmailService
from src.utils.enums import EmailSendingStatus, EmailSortField, EmailType, OrderBy
from tests.factories import make_email, make_system_admin, make_teacher


class TestGetEmails:
    async def test_returns_all_emails_when_no_filters(self, session: AsyncSession):
        await make_email(session, status=EmailSendingStatus.PENDING)
        await make_email(session, status=EmailSendingStatus.SENT)
        await make_email(session, status=EmailSendingStatus.FAILED)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=10,
            filters=SearchEmailAdmin(),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert emails.total == 3

    async def test_filter_by_status_failed(self, session: AsyncSession):
        await make_email(session, status=EmailSendingStatus.FAILED)
        await make_email(session, status=EmailSendingStatus.SENT)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=10,
            filters=SearchEmailAdmin(status=EmailSendingStatus.FAILED),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        print(emails)

        assert emails.total == 1
        assert emails.items[0].status == EmailSendingStatus.FAILED

    async def test_filter_by_status_sent(self, session: AsyncSession):
        await make_email(session, status=EmailSendingStatus.SENT)
        await make_email(session, status=EmailSendingStatus.FAILED)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=10,
            filters=SearchEmailAdmin(status=EmailSendingStatus.SENT),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert emails.total == 1
        assert emails.items[0].status == EmailSendingStatus.SENT

    async def test_filter_by_status_pending(self, session: AsyncSession):
        await make_email(session, status=EmailSendingStatus.PENDING)
        await make_email(session, status=EmailSendingStatus.FAILED)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=10,
            filters=SearchEmailAdmin(status=EmailSendingStatus.PENDING),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert emails.total == 1
        assert emails.items[0].status == EmailSendingStatus.PENDING

    async def test_filter_by_email_type(self, session: AsyncSession):
        target = await make_email(session, email_type=EmailType.INVITE)
        await make_email(session, email_type=EmailType.FORGOT_PASSWORD)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=10,
            filters=SearchEmailAdmin(email_type=EmailType.INVITE),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {e.id for e in emails.items}

        assert emails.total == 1
        assert target.id in returned_ids

    async def test_filter_by_triggered_by(self, session: AsyncSession):
        admin = await make_system_admin(session)
        other_admin = await make_system_admin(session)

        target = await make_email(session, triggered_by=admin.id)
        await make_email(session, triggered_by=other_admin.id)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=10,
            filters=SearchEmailAdmin(triggered_by=admin.id),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {e.id for e in emails.items}

        assert emails.total == 1
        assert target.id in returned_ids

    async def test_filter_by_recipient_user_id(self, session: AsyncSession):
        teacher = await make_teacher(session)
        other_teacher = await make_teacher(session)

        target = await make_email(session, recipient_user_id=teacher.id)
        await make_email(session, recipient_user_id=other_teacher.id)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=10,
            filters=SearchEmailAdmin(recipient_user_id=teacher.id),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {e.id for e in emails.items}

        assert emails.total == 1
        assert target.id in returned_ids

    async def test_combined_filters(self, session: AsyncSession):
        admin = await make_system_admin(session)

        target = await make_email(
            session,
            status=EmailSendingStatus.FAILED,
            email_type=EmailType.INVITE,
            triggered_by=admin.id,
        )
        await make_email(
            session,
            status=EmailSendingStatus.FAILED,
            email_type=EmailType.INVITE,
        )

        emails = await PendingEmailService.get_emails(
            session,
            filters=SearchEmailAdmin(
                status=EmailSendingStatus.FAILED,
                email_type=EmailType.INVITE,
                triggered_by=admin.id,
            ),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        returned_ids = {e.id for e in emails.items}

        assert emails.total == 1
        assert target.id in returned_ids

    async def test_returns_empty_when_no_match(self, session: AsyncSession):
        await make_email(session, status=EmailSendingStatus.PENDING)

        emails = await PendingEmailService.get_emails(
            session,
            filters=SearchEmailAdmin(status=EmailSendingStatus.FAILED),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert emails.total == 0
        assert emails.items == []

    async def test_has_more_true_when_results_exceed_limit(self, session: AsyncSession):
        for _ in range(3):
            await make_email(session)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=2,
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(emails.items) == 2
        assert emails.total == 3

    async def test_has_more_false_on_final_page(self, session: AsyncSession):
        for _ in range(3):
            await make_email(session)

        emails = await PendingEmailService.get_emails(
            session,
            skip=2,
            limit=2,
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(emails.items) == 1
        assert emails.total == 3

    async def test_skip_zero_returns_first_page(self, session: AsyncSession):
        for _ in range(5):
            await make_email(session)

        emails = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=3,
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.DESC,
        )

        assert len(emails.items) == 3
        assert emails.total == 5

    async def test_sort_by_sent_at_descending(self, session: AsyncSession):
        from datetime import UTC, datetime, timedelta

        earlier = await make_email(
            session,
            status=EmailSendingStatus.SENT,
            sent_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        later = await make_email(
            session,
            status=EmailSendingStatus.SENT,
            sent_at=datetime(2024, 6, 1, tzinfo=UTC),
        )

        emails = await PendingEmailService.get_emails(
            session,
            sort_by=EmailSortField.SENT_AT,
            order=OrderBy.DESC,
        )

        ids_in_order = [e.id for e in emails.items]

        assert ids_in_order.index(later.id) < ids_in_order.index(earlier.id)

    async def test_sort_by_sent_at_ascending(self, session: AsyncSession):
        from datetime import UTC, datetime

        earlier = await make_email(
            session,
            status=EmailSendingStatus.SENT,
            sent_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        later = await make_email(
            session,
            status=EmailSendingStatus.SENT,
            sent_at=datetime(2024, 6, 1, tzinfo=UTC),
        )

        emails = await PendingEmailService.get_emails(
            session,
            sort_by=EmailSortField.SENT_AT,
            order=OrderBy.ASC,
        )

        ids_in_order = [e.id for e in emails.items]

        assert ids_in_order.index(earlier.id) < ids_in_order.index(later.id)

    async def test_invalid_sort_field_falls_back_to_created_at(
        self, session: AsyncSession
    ):
        await make_email(session)
        await make_email(session)

        emails = await PendingEmailService.get_emails(
            session, sort_by="not_a_real_field", order=OrderBy.DESC
        )

        assert emails.total == 2

    async def test_service_returns_paginated_response(self, session: AsyncSession):
        for _ in range(3):
            await make_email(session)

        result = await PendingEmailService.get_emails(
            session,
            skip=0,
            limit=2,
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.ASC,
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.has_more is True

    async def test_service_has_more_false_on_last_page(self, session: AsyncSession):
        for _ in range(3):
            await make_email(session)

        result = await PendingEmailService.get_emails(
            session,
            skip=2,
            limit=2,
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.ASC,
        )

        assert result.has_more is False

    async def test_service_filter_propagates_to_repo(self, session: AsyncSession):
        await make_email(session, status=EmailSendingStatus.FAILED)
        await make_email(session, status=EmailSendingStatus.SENT)

        result = await PendingEmailService.get_emails(
            session,
            filters=SearchEmailAdmin(status=EmailSendingStatus.FAILED),
            sort_by=EmailSortField.CREATED_AT,
            order=OrderBy.ASC,
        )

        assert result.total == 1
        assert result.items[0].status == EmailSendingStatus.FAILED
