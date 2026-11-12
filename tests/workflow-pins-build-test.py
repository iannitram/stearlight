#!/usr/bin/env python3
"""Locked tests: every action in build.yml is pinned to a full commit SHA."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# action -> (commit SHA of the tag named in the comment, tag)
PINS = {
    'actions/checkout': ('11d5960a326750d5838078e36cf38b85af677262', 'v4'),
    'actions/setup-java': ('cf277c60eb25467037889841efdb72551f06f6c3', 'v4'),
    'docker/setup-buildx-action': ('8d2750c68a42422c14e847fe6c8ac0403b4cbd6f', 'v3'),
    'actions/upload-artifact': ('ea165f8d65b6e75b540449e92b4886f43607fa02', 'v4'),
    'android-actions/setup-android': ('9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407', 'v3'),
    'gradle/actions/setup-gradle': ('ed408507eac070d1f99cc633dbcf757c94c7933a', 'v4'),
    'actions/cache': ('0057852bfaa89a56745cba8c7296529d2fc39830', 'v4'),
    'actions/download-artifact': ('d3f86a106a0bac45b974a628896c90dbdf5c8093', 'v4'),
}
FILES = {
    'build.yml': 16,
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
