#!/usr/bin/env python3
"""Locked tests: the tracking publication test is time-bounded and run by check.sh."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = [line.strip() for line in (ROOT / 'build_files/quest/check.sh').read_text().splitlines()
           if line.strip() and not line.lstrip().startswith('#')]
TEST = 'packages/quest-runtime/tests/tracking-publication.test.cpp'
SOURCE = (ROOT / TEST).read_text()


def compile_index():
    return next((i for i, line in enumerate(RUNNERS) if line.startswith('g++ ') and TEST in line), None)


class TrackingBoundTest(unittest.TestCase):
    def test_reader_child_arms_a_30_second_alarm_right_after_fork(self):
        self.assertRegex(SOURCE, r'if\s*\(\s*!reader\s*\)\s*\{\s*alarm\(30\);')

    def test_alarm_is_declared_through_unistd(self):
        self.assertIn('#include <unistd.h>', SOURCE)

    def test_parent_still_requires_a_normal_zero_exit(self):
        self.assertIn('assert(WIFEXITED(status)&&WEXITSTATUS(status)==0);', SOURCE)

    def test_reader_still_exits_zero_on_the_final_sample(self):
        self.assertIn('if(sample.width==100000){assert(reads>0);_exit(0);}', SOURCE)


class TrackingWiringTest(unittest.TestCase):
    def test_check_compiles_the_test(self):
        self.assertIsNotNone(compile_index(), TEST + ' is not compiled by check.sh')

    def test_compile_line_uses_the_strict_flags(self):
        line = RUNNERS[compile_index()]
        for flag in ('-std=c++17', '-Wall', '-Wextra', '-Werror'):
            with self.subTest(flag=flag):
                self.assertIn(' ' + flag + ' ', line)
        self.assertNotIn('NDEBUG', line)

    def test_the_built_binary_is_run_on_the_next_line(self):
        output = re.search(r'-o "(\$\w+)"', RUNNERS[compile_index()])
        self.assertIsNotNone(output, 'the compile line needs -o "$variable"')
        self.assertEqual(RUNNERS[compile_index() + 1], '"' + output.group(1) + '"')

    def test_the_binary_variable_is_set_before_it_is_used(self):
        variable = re.search(r'-o "\$(\w+)"', RUNNERS[compile_index()]).group(1)
        self.assertTrue(any(line.startswith(variable + '=$(mktemp)') for line in RUNNERS[:compile_index()]))


if __name__ == '__main__':
    unittest.main()
