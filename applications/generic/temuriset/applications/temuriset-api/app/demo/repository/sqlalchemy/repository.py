"""Find and remove the demo namespace: everything owned by accounts of kind ``demo`` and their parties."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Children before parents, so no RESTRICT foreign key blocks a delete. Audit and outbox events stay: they are history.
_DELETES = (
    "UPDATE opportunities SET current_version_id = NULL WHERE partner_party_id = ANY(:parties)",
    "UPDATE partner_profiles SET general_intake_version_id = NULL WHERE party_id = ANY(:parties)",
    "DELETE FROM pitches WHERE requester_party_id = ANY(:parties) OR recipient_party_id = ANY(:parties)",
    "DELETE FROM preflights WHERE actor_party_id = ANY(:parties)",
    "DELETE FROM match_runs WHERE actor_party_id = ANY(:parties)",
    "DELETE FROM saved_items WHERE party_id = ANY(:parties)",
    "DELETE FROM relevance_feedback WHERE party_id = ANY(:parties)",
    "DELETE FROM search_documents WHERE owner_party_id = ANY(:parties)",
    "DELETE FROM external_handoffs WHERE partner_party_id = ANY(:parties) OR actor_party_id = ANY(:parties)",
    "DELETE FROM opportunities WHERE partner_party_id = ANY(:parties)",
    "DELETE FROM partner_profiles WHERE party_id = ANY(:parties)",
    "DELETE FROM funding_requests WHERE owner_party_id = ANY(:parties)",
    "DELETE FROM legal_entities WHERE owner_party_id = ANY(:parties)",
    "DELETE FROM support_requests WHERE owner_party_id = ANY(:parties)",
    "DELETE FROM inventions WHERE managing_party_id = ANY(:parties)",
    "DELETE FROM documents WHERE owner_party_id = ANY(:parties)",
    "DELETE FROM jobs WHERE actor_party_id = ANY(:parties)",
    # Recreated rows keep their ids, so a remembered answer would otherwise replay over the new state.
    "DELETE FROM idempotency_records WHERE actor_party_id = ANY(:parties)",
    "DELETE FROM invitations WHERE invited_by_account_id = ANY(:accounts)",
    "DELETE FROM parties WHERE id = ANY(:parties)",
    "DELETE FROM organizations WHERE id = ANY(:organizations)",
    "DELETE FROM accounts WHERE id = ANY(:accounts)",
)


class SqlAlchemyDemoRepository:
    """The demo namespace in the database."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The caller's session.
        """
        self.session = session

    async def namespace(self) -> tuple[list[UUID], list[UUID], list[UUID]]:
        """Return demo accounts, their parties, and organizations whose every member is a demo account.

        Returns:
            tuple[list[UUID], list[UUID], list[UUID]]: Accounts, parties and organizations.
        """
        accounts = list(await self.session.scalars(text("SELECT id FROM accounts WHERE kind = 'demo'")))
        organizations = list(
            await self.session.scalars(
                text(
                    "SELECT organization_id FROM memberships GROUP BY organization_id "
                    "HAVING bool_and(account_id = ANY(:accounts))"
                ),
                {"accounts": accounts},
            )
        )
        parties = list(
            await self.session.scalars(
                text(
                    "SELECT id FROM parties WHERE account_id = ANY(:accounts) OR organization_id = ANY(:organizations)"
                ),
                {"accounts": accounts, "organizations": organizations},
            )
        )
        return accounts, parties, organizations

    async def remove_namespace(self) -> int:
        """Delete every demo row; real accounts and what they own are untouched.

        Returns:
            int: Demo accounts removed.
        """
        accounts, parties, organizations = await self.namespace()
        if not accounts:
            return 0
        values = {"accounts": accounts, "parties": parties, "organizations": organizations}
        for statement in _DELETES:
            await self.session.execute(text(statement), values)
        return len(accounts)
