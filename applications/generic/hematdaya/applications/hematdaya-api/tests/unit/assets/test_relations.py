"""Containment cycle rule."""

from uuid import uuid4

from app.assets.service.relations import MAX_DEPTH, would_create_cycle


def test_cycles_and_self_references_are_detected() -> None:
    """
    Condition:
    - Meter contains Circuit contains Kulkas.

    Expected:
    - Kulkas containing Meter, or Meter containing itself, is a cycle; Meter containing TV is not.
    """
    meter, circuit, kulkas, tv = uuid4(), uuid4(), uuid4(), uuid4()
    edges = [(meter, circuit), (circuit, kulkas)]

    assert would_create_cycle(edges, kulkas, meter)
    assert would_create_cycle(edges, meter, meter)
    assert not would_create_cycle(edges, meter, tv)


def test_unbounded_chains_are_refused() -> None:
    """
    Condition:
    - A containment chain longer than the walk limit.

    Expected:
    - The rule refuses rather than walking forever.
    """
    nodes = [uuid4() for _ in range(MAX_DEPTH + 2)]
    edges = list(zip(nodes, nodes[1:], strict=False))

    assert would_create_cycle(edges, uuid4(), nodes[0])
