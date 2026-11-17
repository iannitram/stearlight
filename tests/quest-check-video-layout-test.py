#!/usr/bin/env python3
"""Locked tests: check.sh builds and runs the linear NV12 layout test, and CI has the Vulkan headers."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = [line.strip() for line in (ROOT / 'build_files/quest/check.sh').read_text().splitlines()
           if line.strip() and not line.lstrip().startswith('#')]
WORKFLOW = (ROOT / '.github/workflows/build.yml').read_text()
TEST = 'packages/quest-runtime/tests/video-image-layout.test.cpp'


def compile_index():
    return next((i for i, line in enumerate(RUNNERS) if line.startswith('g++ ') and TEST in line), None)


class VideoLayoutWiringTest(unittest.TestCase):
    def test_check_compiles_the_layout_test(self):
        self.assertIsNotNone(compile_index(), TEST + ' is not compiled by check.sh')

    def test_compile_line_uses_the_strict_flags_and_the_header_directory(self):
        line = RUNNERS[compile_index()]
        for flag in ('-std=c++17', '-Wall', '-Wextra', '-Werror', '-Ipackages/quest-runtime/linux'):
            with self.subTest(flag=flag):
                self.assertIn(' ' + flag + ' ', line)

    def test_compile_line_does_not_disable_asserts(self):
        self.assertNotIn('NDEBUG', RUNNERS[compile_index()])

    def test_the_built_binary_is_run_on_the_next_line(self):
        output = re.search(r'-o "(\$\w+)"', RUNNERS[compile_index()])
        self.assertIsNotNone(output, 'the compile line needs -o "$variable"')
        self.assertEqual(RUNNERS[compile_index() + 1], '"' + output.group(1) + '"')

    def test_the_binary_variable_is_set_before_it_is_used(self):
        variable = re.search(r'-o "\$(\w+)"', RUNNERS[compile_index()]).group(1)
        before = RUNNERS[:compile_index()]
        self.assertTrue(any(line.startswith(variable + '=$(mktemp)') for line in before), variable)

    def test_source_checks_installs_the_vulkan_headers(self):
        job = WORKFLOW.split('  source-checks:\n', 1)[1].split('\n  quest-rootfs:', 1)[0]
        apt = [line for line in job.splitlines() if 'apt-get install' in line]
        self.assertEqual(len(apt), 1, apt)
        self.assertRegex(apt[0], r'(^|\s)libvulkan-dev(\s|$)')


if __name__ == '__main__':
    unittest.main()
