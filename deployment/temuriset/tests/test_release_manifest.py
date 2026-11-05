"""Release metadata rejects mutable references and mismatched promotion evidence."""

import unittest

from deployment.temuriset.release_manifest import build_manifest, verify_promotion

DIGEST = "sha256:" + "a" * 64
SHA = "b" * 40
RUNTIME = [
    {
        "schema_version": 1,
        "alembic_head": "0009",
        "infrastructure_images": {service: f"example/{service}:1@{DIGEST}" for service in (
            "postgres", "object-store", "clamav", "edge",
        )},
        "source_release": "0.1.0",
        "composition": {"id": name, "version": 1},
        "capabilities": [{"id": "core", "status": "planned", "optional": False}],
        "adapters": [{"id": "object-storage", "implementation": "s3", "status": "available"}],
        "policies": [],
    }
    for name in ("generic-base", "generic-with-review", "project-support-only")
]


class ManifestTests(unittest.TestCase):
    """Exercise the release and promotion contracts."""

    def test_release_rejects_mutable_image(self) -> None:
        with self.assertRaises(ValueError):
            build_manifest(SHA, "temuriset-v0.1.0", "0009", "ghcr.io/example/api:latest", "web@" + DIGEST, RUNTIME)

    def test_runtime_schema_must_match_the_declared_alembic_head(self) -> None:
        with self.assertRaisesRegex(ValueError, "Runtime infrastructure and schema"):
            build_manifest(SHA, "temuriset-v0.1.0", "0010", "api@" + DIGEST, "web@" + DIGEST, RUNTIME)

    def test_promotion_requires_the_same_release_images_and_all_journeys(self) -> None:
        manifest = build_manifest(
            SHA, "temuriset-v0.1.0", "0009", "ghcr.io/example/api@" + DIGEST,
            "ghcr.io/example/web@" + DIGEST, RUNTIME, published=True,
        )
        evidence = {
            "environment": "staging",
            "url": "https://staging.example.test",
            "composition": "generic-base",
            "commit": SHA,
            "images": manifest["images"],
            "checks": {name: "passed" for name in ("003", "J01", "J02", "J03", "J04", "J05", "restore", "compat")},
        }
        verify_promotion(manifest, evidence, "generic-base")
        for changed in (
            {**evidence, "images": {**manifest["images"], "web": "web@" + "sha256:" + "c" * 64}},
            {**evidence, "composition": "project-support-only"},
            {**evidence, "checks": {**evidence["checks"], "J05": "skipped"}},
        ):
            with self.assertRaises(ValueError):
                verify_promotion(manifest, changed, "generic-base")


if __name__ == "__main__":
    unittest.main()
