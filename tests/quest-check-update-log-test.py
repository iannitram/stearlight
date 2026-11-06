#!/usr/bin/env python3
"""Locked tests: check.sh builds and runs the update log test."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = [line.strip() for line in (ROOT / 'build_files/quest/check.sh').read_text().splitlines()
           if line.strip() and not line.lstrip().startswith('#')]
TEST = 'packages/quest-runtime/tests/update-log.test.cpp'


class CheckWiringTest(unittest.TestCase):
    def setUp(self):
        self.index = next((i for i, line in enumerate(RUNNERS) if line.startswith('g++ ') and TEST in line), None)
        self.assertIsNotNone(self.index, TEST + ' is not built by check.sh')
        self.line = RUNNERS[self.index]

    def test_compile_line_uses_the_strict_flags(self):
        for flag in ('-std=c++17', '-Wall', '-Wextra', '-Werror'):
            with self.subTest(flag=flag):
                self.assertIn(' ' + flag + ' ', self.line)
        self.assertNotIn('NDEBUG', self.line)

    def test_the_built_binary_is_run_on_the_next_line(self):
        output = re.search(r'-o "(\$\w+)"', self.line)
        self.assertIsNotNone(output, 'the compile line needs -o "$variable"')
        self.assertEqual(RUNNERS[self.index + 1], '"' + output.group(1) + '"')

    def test_the_binary_variable_is_set_before_it_is_used(self):
        variable = re.search(r'-o "\$(\w+)"', self.line).group(1)
        self.assertTrue(any(line.startswith(variable + '=$(mktemp)') for line in RUNNERS[:self.index]), variable)


if __name__ == '__main__':
    unittest.main()
