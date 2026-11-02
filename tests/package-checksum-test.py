"""Verify the Windows package hash list covers the launchers and QEMU tree."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageChecksumTest(unittest.TestCase):
    def setUp(self):
        self.runtime = (ROOT / "packages/windows-runtime/build-runtime.sh").read_text()
        self.package = (ROOT / "post_process/package-windows.ps1").read_text()

    def test_hash_list_covers_launchers_and_qemu_tree(self):
        self.assertIn("sha256sum start-vm.ps1 start-vm.cmd", self.runtime)
        self.assertIn("find qemu -type f -print0", self.runtime)

    def test_hash_lines_append_to_package_folder(self):
        self.assertIn('sums="$(dirname "$output")/SHA256SUMS"', self.runtime)
        self.assertIn(') >> "$sums"', self.runtime)
        self.assertNotIn(") >> SHA256SUMS", self.runtime)

    def test_package_rejects_missing_or_replaced_qemu_entries(self):
        self.assertIn("Checksum mismatch: $file", self.package)
        self.assertIn("Missing checksum entry", self.package)
        self.assertIn(
            "Get-ChildItem -LiteralPath (Join-Path $package 'qemu') -Recurse -File",
            self.package,
        )
        for name in ("start-vm.ps1", "start-vm.cmd"):
            self.assertIn(name, self.package)

    def test_runtime_writes_text_hash_lines(self):
        self.assertIn("sed 's/ \\*/  /'", self.runtime)

    def test_package_strips_leading_star_from_file_name(self):
        self.assertIn("$file -replace '^\\*'", self.package)


if __name__ == "__main__":
    unittest.main()
