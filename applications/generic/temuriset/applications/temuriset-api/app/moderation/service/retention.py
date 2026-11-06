"""Versioned retention-policy answers for privacy requests."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.service import anonymize_personal_party, personal_party_id
from app.core.errors.base import AppError
from app.core.settings import get_settings
from app.documents.service.service import REVOKED_MESSAGE, DocumentService
from app.funding.service.service import FundingService
from app.identity.service.service import IdentityService
from app.intake.service.service import IntakeService
from app.moderation.model.schema import CategoryRetained, CategoryToRemove, PrivacyAnswer
from app.moderation.repository.sqlalchemy.repository import SqlAlchemyModerationRepository
from app.needs.service.service import NeedsService
from app.portfolio.service.service import PortfolioService

_REMOVABLE = frozenset({"sign_in_records", "public_listings", "private_documents", "account_profile"})


async def deletion_answer(session: AsyncSession, account_id: UUID) -> tuple[PrivacyAnswer, str]:
    """Generate a planned answer from the current policy without claiming a removal."""
    repository = SqlAlchemyModerationRepository(session)
    policies = await repository.policies()
    holds = {hold.category_key: hold for hold in await repository.active_holds(account_id)}
    versions = {row.policy_version for row in policies}
    if len(versions) != 1 or any(row.decision == "REMOVE" and row.key not in _REMOVABLE for row in policies):
        raise AppError()
    planned = []
    retained = []
    for row in policies:
        hold = holds.get(row.key)
        if hold is not None:
            retained.append(CategoryRetained(key=row.key, label=row.label, reason=hold.reason, period=hold.period))
        elif row.decision == "RETAIN":
            retained.append(CategoryRetained(key=row.key, label=row.label, reason=row.reason, period=row.period))
        else:
            planned.append(CategoryToRemove(key=row.key, label=row.label))
    return PrivacyAnswer(
        to_remove=planned,
        removed=[],
        retained=retained,
        notice=REVOKED_MESSAGE + " Cadangan tetap disimpan sampai masa simpannya berakhir.",
    ), versions.pop()


async def prepare_deletion(session: AsyncSession, account_id: UUID, answer: PrivacyAnswer) -> None:
    """Apply transactional removals and prepare private files for physical erasure."""
    keys = {item.key for item in answer.to_remove}
    identity = IdentityService(session, get_settings())
    await identity.freeze_for_deletion(account_id, remove_sign_in="sign_in_records" in keys)
    party_id = await personal_party_id(session, account_id)
    if "public_listings" in keys:
        await PortfolioService(session).withdraw_personal_listings(party_id)
        await NeedsService(session).withdraw_personal_listings(party_id)
        await FundingService(session).withdraw_personal_listings(party_id)
        await IntakeService(session).withdraw_personal_listings(party_id)
    if "private_documents" in keys:
        await DocumentService(session, get_settings()).prepare_party_erasure(party_id)


async def complete_deletion(session: AsyncSession, account_id: UUID, answer: PrivacyAnswer) -> str:
    """Erase prepared files, finish account anonymization and return the outcome destination."""
    keys = {item.key for item in answer.to_remove}
    identity = IdentityService(session, get_settings())
    if "private_documents" in keys:
        party_id = await personal_party_id(session, account_id)
        await DocumentService(session, get_settings()).erase_party_bytes(party_id)
    if "account_profile" in keys:
        await anonymize_personal_party(session, account_id)
        return await identity.anonymize_for_deletion(account_id)
    return await identity.deletion_address(account_id)
