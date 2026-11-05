"""Spec 038 preflight checks protect real data before any restore mutation."""

import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from deployment.temuriset.backup import backup_tools as backup


class BackupSafetyTests(unittest.TestCase):
    """Exercise dangerous inputs without a database or object-store credential."""

    def setUp(self) -> None:
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_archive_rejects_links_and_parent_paths(self) -> None:
        for name, kind in [
            ("../escape", tarfile.REGTYPE),
            ("snapshot.json", tarfile.SYMTYPE),
        ]:
            with self.subTest(name=name, kind=kind):
                bundle = self.directory / "input.tar"
                with tarfile.open(bundle, "w") as archive:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    archive.addfile(member)
                with self.assertRaises(backup.BackupError):
                    destination = self.directory / name.encode().hex()
                    destination.mkdir()
                    backup.extract_archive(bundle, destination)

    def test_archive_rejects_duplicate_member(self) -> None:
        bundle = self.directory / "input.tar"
        with tarfile.open(bundle, "w") as archive:
            for _ in range(2):
                member = tarfile.TarInfo("snapshot.json")
                member.size = 2
                archive.addfile(member, io.BytesIO(b"{}"))
        with self.assertRaises(backup.BackupError):
            backup.extract_archive(bundle, self.directory)

    def test_target_names_must_share_isolated_identifier(self) -> None:
        for database, bucket in [
            ("temuriset", "temuriset-restore-drill"),
            ("temuriset_restore_drill", "temuriset-documents"),
            ("temuriset_restore_drill", "temuriset-restore-other"),
        ]:
            with (
                self.subTest(database=database, bucket=bucket),
                self.assertRaises(backup.BackupError),
            ):
                backup.restore_target_id(database, bucket)
        self.assertEqual(
            backup.restore_target_id(
                "temuriset_restore_drill", "temuriset-restore-drill"
            ),
            "drill",
        )

    def test_missing_or_public_keyfile_is_refused(self) -> None:
        keyfile = self.directory / "key"
        with self.assertRaises(backup.BackupError):
            backup.passphrase_file(keyfile)
        keyfile.write_text("synthetic-test-passphrase")
        keyfile.chmod(0o644)
        with self.assertRaises(backup.BackupError):
            backup.passphrase_file(keyfile)
        keyfile.chmod(0o600)
        self.assertEqual(backup.passphrase_file(keyfile), keyfile)

    def test_tampered_archive_is_refused_before_decryption(self) -> None:
        artifact = self.directory / "archive.tar.gpg"
        artifact.write_bytes(b"original")
        trusted_digest = backup.file_digest(artifact)
        artifact.write_bytes(b"tampered")
        with self.assertRaises(backup.BackupError):
            backup.verify_archive_digest(artifact, trusted_digest)

    def test_pair_refuses_missing_or_changed_document(self) -> None:
        expected = [{"key": "document", "size": 4, "sha256": "a" * 64}]
        with self.assertRaises(backup.BackupError):
            backup.verify_document_pair(expected, [])
        with self.assertRaises(backup.BackupError):
            backup.verify_document_pair(
                expected, [{"key": "document", "size": 4, "sha256": "b" * 64}]
            )
        backup.verify_document_pair(expected, expected)

    def test_prune_only_removes_old_regular_bundle_with_explicit_apply(self) -> None:
        old = self.directory / "temuriset-20261105T000000Z-12345678.tar.gpg"
        recent = self.directory / "temuriset-20261106T000000Z-abcdefab.tar.gpg"
        unrelated = self.directory / "important.txt"
        linked = self.directory / "temuriset-20261105T000000Z-abcdef12.tar.gpg"
        old.write_bytes(b"encrypted fixture")
        unrelated.write_text("preserve")
        linked.symlink_to(unrelated)
        os.utime(old, (0, 0))
        self.assertEqual(backup.prune(self.directory, days=1, apply=False), [old.name])
        self.assertTrue(old.exists())
        with self.assertRaises(backup.BackupError):
            backup.prune(self.directory, days=1, apply=True)
        recent.write_bytes(b"new encrypted fixture")
        self.assertEqual(backup.prune(self.directory, days=1, apply=True), [old.name])
        self.assertFalse(old.exists())
        self.assertTrue(recent.is_file())
        self.assertTrue(linked.is_symlink())
        self.assertTrue(unrelated.is_file())
