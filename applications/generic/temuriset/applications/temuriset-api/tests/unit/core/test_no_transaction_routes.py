"""Product boundary: TemuRiset records agreements; it never moves money or issues shares (PRD section 2)."""

import re

from app.main import app

TRANSACTION = re.compile(
    r"payment|payout|escrow|wallet|checkout|money[-_]?transfer|valuation|share[-_]?issu|securities|crowdfund|cap[-_]?table",
    re.IGNORECASE,
)


def test_no_route_moves_money_or_issues_shares() -> None:
    """
    Condition:
    - The full route table of the application.

    Expected:
    - No path or operation offers payment, custody, valuation, share issuance or crowdfunding.
    """
    document = app.openapi()

    for path, path_item in document["paths"].items():
        assert not TRANSACTION.search(path)
        for operation in path_item.values():
            assert not TRANSACTION.search(operation.get("operationId", ""))
