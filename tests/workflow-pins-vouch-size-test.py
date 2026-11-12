#!/usr/bin/env python3
"""Locked tests: every action in pr-vouch.yml and pr-size.yml is pinned to a full commit SHA."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# action -> (commit SHA of the tag named in the comment, tag)
PINS = {
    'actions/github-script': ('ed597411d8f924073f98dfc5c65a23a2325f34cd', 'v8'),
    'actions/checkout': ('11d5960a326750d5838078e36cf38b85af677262', 'v4'),
    'mitchellh/vouch/action/check-user': ('d66fa29a64600490892131ad87597c30c91fcac4', 'v1'),
}
FILES = {
    'pr-vouch.yml': 3,
    'pr-size.yml': 4,
}
USES = re.compile(r'^\s*(?:- )?uses: (\S+)(?: +# (\S+))?\s*$')


def uses_lines(name):
    lines = (ROOT / '.github/workflows' / name).read_text().splitlines()
    return [USES.match(line).groups() for line in lines if re.match(r'^\s*(?:- )?uses:', line)]


class PinnedActionsTest(unittest.TestCase):
    def test_every_uses_line_is_still_there(self):
        for name, count in FILES.items():
            with self.subTest(file=name):
                self.assertEqual(len(uses_lines(name)), count)

    def test_every_action_names_a_full_commit_sha(self):
        for name in FILES:
            for reference, _ in uses_lines(name):
                with self.subTest(file=name, uses=reference):
                    self.assertRegex(reference, r'@[0-9a-f]{40}$')

    def test_each_sha_is_the_expected_commit_for_its_action(self):
        for name in FILES:
            for reference, tag in uses_lines(name):
                action, _, sha = reference.partition('@')
                with self.subTest(file=name, uses=reference):
                    self.assertEqual(sha, PINS[action][0])

    def test_each_line_carries_a_comment_with_the_tag_it_came_from(self):
        for name in FILES:
            for reference, tag in uses_lines(name):
                with self.subTest(file=name, uses=reference):
                    self.assertEqual(tag, PINS[reference.partition('@')[0]][1])

    def test_no_uses_line_names_a_tag_or_branch(self):
        for name in FILES:
            text = (ROOT / '.github/workflows' / name).read_text()
            with self.subTest(file=name):
                self.assertNotRegex(text, r'uses: \S+@v\d')
                self.assertNotRegex(text, r'uses: \S+@(main|master)\b')


if __name__ == '__main__':
    unittest.main()
