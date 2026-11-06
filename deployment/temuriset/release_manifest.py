"""Build immutable release inventories and verify operator-supplied promotion evidence."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

_SCHEMA = Path(__file__).with_name("release-manifest.schema.json")
_COMPOSITIONS = {"generic-base", "generic-with-review", "project-support-only"}
_CHECKS = {"003", "J01", "J02", "J03", "J04", "J05", "restore", "compat"}


def validate_manifest(manifest: dict) -> None:
    """Reject malformed metadata, mutable image references and missing composition checks."""
    validator = Draft202012Validator(json.loads(_SCHEMA.read_text()))
    if not validator.is_valid(manifest):
        raise ValueError("Release manifest violates its schema.")
    if {item["id"] for item in manifest["compositions"]} != _COMPOSITIONS:
        raise ValueError("Inventory must cover all supported compositions.")
    if manifest["images"]["worker"] != manifest["images"]["api"]:
        raise ValueError("API and worker must share one immutable image.")
    for item in manifest["compositions"]:
        if not any(
            adapter["id"] == "object-storage" and adapter.get("implementation") == "s3"
            for adapter in item["adapters"]
        ):
            raise ValueError("Release smoke must use the S3 runtime adapter.")


def build_manifest(
    commit: str,
    tag: str,
    alembic_head: str,
    api: str,
    web: str,
    smoke_inventory: list[dict],
    *,
    published: bool = False,
) -> dict:
    """Summarize only the allowlisted version fields from completed composition smoke."""
    try:
        infrastructure = smoke_inventory[0]["infrastructure_images"]
        if any(
            item["infrastructure_images"] != infrastructure or item["alembic_head"] != alembic_head
            for item in smoke_inventory
        ):
            raise ValueError("Runtime infrastructure and schema must match every composition smoke.")
        compositions = [
            {
                "id": item["composition"]["id"],
                "version": item["composition"]["version"],
                "source_release": item["source_release"],
                "capability_schema": item["schema_version"],
                "capabilities": item["capabilities"],
                "adapters": item["adapters"],
                "policies": item["policies"],
                "smoke": "passed",
            }
            for item in smoke_inventory
        ]
    except (IndexError, KeyError, TypeError):
        raise ValueError("Composition smoke inventory is incomplete.") from None
    manifest = {
        "schema_version": 1,
        "commit": commit,
        "tag": tag,
        "configuration": {"version": 1, "web_api_origin": "http://api:8000"},
        "alembic_head": alembic_head,
        "images": {"api": api, "worker": api, "web": web},
        "infrastructure_images": infrastructure,
        "compositions": sorted(compositions, key=lambda item: item["id"]),
        "publication": "published" if published else "candidate",
        "rollouts": [],
    }
    validate_manifest(manifest)
    return manifest


def verify_promotion(manifest: dict, evidence: dict, composition: str) -> None:
    """Bind trusted staging evidence to this published release and selected composition."""
    validate_manifest(manifest)
    if manifest["publication"] != "published":
        raise ValueError("Production promotion requires a published release.")
    try:
        origin = urlsplit(evidence.get("url", ""))
        trusted_shape = (
            origin.scheme == "https" and origin.hostname
            and not any((origin.username, origin.password, origin.query, origin.fragment))
            and origin.path in ("", "/")
        )
    except (ValueError, TypeError, AttributeError):
        trusted_shape = False
    if not trusted_shape or evidence.get("environment") != "staging":
        raise ValueError("Promotion requires staging HTTPS evidence.")
    if (
        composition not in _COMPOSITIONS
        or evidence.get("composition") != composition
        or evidence.get("commit") != manifest["commit"]
        or evidence.get("images") != manifest["images"]
    ):
        raise ValueError("Staging evidence does not match the release and composition.")
    checks = evidence.get("checks")
    if not isinstance(checks, dict) or not all(checks.get(check) == "passed" for check in _CHECKS):
        raise ValueError("Browser journeys, restore and compatibility evidence must all pass.")


def main() -> None:
    """Generate a release manifest or check an operator-approved promotion record."""
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="action", required=True)
    build = subcommands.add_parser("build")
    for option in ("commit", "tag", "alembic-head", "api", "web"):
        build.add_argument("--" + option, required=True)
    build.add_argument("--inventory", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--published", action="store_true")
    promote = subcommands.add_parser("verify-promotion")
    promote.add_argument("--manifest", required=True, type=Path)
    promote.add_argument("--evidence", required=True, type=Path)
    promote.add_argument("--composition", required=True)
    args = parser.parse_args()
    try:
        if args.action == "build":
            inventory = [json.loads(line) for line in args.inventory.read_text().splitlines() if line.strip()]
            manifest = build_manifest(
                args.commit, args.tag, args.alembic_head, args.api, args.web, inventory, published=args.published,
            )
            args.output.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        else:
            verify_promotion(json.loads(args.manifest.read_text()), json.loads(args.evidence.read_text()), args.composition)
            print("The supplied staging evidence matches the published release.")
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
