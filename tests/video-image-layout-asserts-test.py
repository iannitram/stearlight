#!/usr/bin/env python3
"""Locked tests: video-image-layout.test.cpp keeps its calls outside assert()."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'packages/quest-runtime/tests/video-image-layout.test.cpp').read_text()


def assert_arguments(text):
    """Yield the text inside each assert( ... ), with balanced parentheses."""
    for match in re.finditer(r'\bassert\s*\(', text):
        depth, index = 1, match.end()
        while depth and index < len(text):
            depth += {'(': 1, ')': -1}.get(text[index], 0)
            index += 1
        yield text[match.end():index - 1]


class AssertSideEffectTest(unittest.TestCase):
    def test_no_assert_argument_calls_linear_video_planes(self):
        for argument in assert_arguments(SOURCE):
            with self.subTest(argument=argument):
                self.assertNotIn('linearVideoPlanes(', argument)

    def test_no_assert_argument_calls_prepare(self):
        for argument in assert_arguments(SOURCE):
            with self.subTest(argument=argument):
                self.assertNotIn('.prepare(', argument)

    def test_no_struct_is_started_with_only_its_stype(self):
        # g++ -Wextra -Werror (-Wmissing-field-initializers) rejects `T x{VK_STRUCTURE_TYPE_...};`.
        self.assertNotRegex(SOURCE, r'\w\s*\{\s*VK_STRUCTURE_TYPE_')

    def test_every_struct_still_gets_its_stype(self):
        for stype in ('IMAGE_CREATE_INFO', 'IMAGE_DRM_FORMAT_MODIFIER_EXPLICIT_CREATE_INFO_EXT',
                      'EXTERNAL_MEMORY_IMAGE_CREATE_INFO', 'IMAGE_FORMAT_LIST_CREATE_INFO'):
            with self.subTest(stype=stype):
                self.assertRegex(SOURCE, r'sType\s*=\s*VK_STRUCTURE_TYPE_' + stype + r'\s*;')

    def test_every_call_is_still_made(self):
        self.assertGreaterEqual(SOURCE.count('linearVideoPlanes('), 8)
        self.assertGreaterEqual(SOURCE.count('.prepare('), 3)

    def test_the_expected_plane_values_are_still_checked(self):
        for value in ('5308416', '2654208', '7962624'):
            with self.subTest(value=value):
                self.assertIn(value, SOURCE)

    def test_the_pass_line_is_still_printed(self):
        self.assertIn('PASS: tall linear NV12 planes, valid layouts and compressed/non-video formats', SOURCE)

    def test_checker_sees_nested_assert_arguments(self):
        found = list(assert_arguments('assert(f(g(1))==2); x; assert(!h());'))
        self.assertEqual(found, ['f(g(1))==2', '!h()'])


if __name__ == '__main__':
    unittest.main()
