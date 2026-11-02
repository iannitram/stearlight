#!/usr/bin/env python3
"""Locked tests: the Windows-host ARM64 disk step uses the Containerfile's Alpine image and a pinned e2fsprogs."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / 'build_files/build-arm64.ps1').read_text()
CONTAINERFILE = (ROOT / 'Containerfile').read_text()
IMAGE = 'alpine:3.24@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6'


class Arm64DiskPinsTest(unittest.TestCase):
    def test_docker_run_uses_the_pinned_alpine_image(self):
        self.assertRegex(SCRIPT, r'-e "STEARLIGHT_DISK_SIZE=\$\{diskSize\}G" ' + re.escape(IMAGE) + r' sh -c')

    def test_the_image_matches_the_containerfile_pin(self):
        self.assertIn('FROM --platform=$TARGETPLATFORM ' + IMAGE + ' AS rootfs', CONTAINERFILE)

    def test_no_floating_alpine_tag_remains(self):
        self.assertNotIn('alpine:edge', SCRIPT)
        for image in re.findall(r'alpine:[\w.]+(?:@sha256:[0-9a-f]+)?', SCRIPT):
            self.assertEqual(image, IMAGE)

    def test_apk_add_names_an_explicit_e2fsprogs_version(self):
        self.assertIn('apk add --no-cache e2fsprogs=1.47.4-r0 >/dev/null', SCRIPT)
        self.assertNotRegex(SCRIPT, r'e2fsprogs(?![=\w-])')

    def test_the_disk_is_still_written_to_the_output_folder(self):
        self.assertIn("cp /work/stearlight-arm64.ext4 /out/stearlight-arm64.ext4", SCRIPT)
        self.assertIn("Join-Path $output 'stearlight-arm64.ext4'", SCRIPT)

    def test_the_disk_commands_are_unchanged(self):
        for command in ('mke2fs -q -F -t ext4 -O ^has_journal,^orphan_file -E lazy_itable_init=0',
                        'e2fsck -fn /work/stearlight-arm64.ext4'):
            with self.subTest(command=command):
                self.assertIn(command, SCRIPT)


if __name__ == '__main__':
    unittest.main()
