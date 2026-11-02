"""Locked tests for lock_patches: only the patches named in sources.lock.json are used."""
import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENUS = ROOT / 'packages' / 'windows-runtime' / 'windows-venus'
# Lock order is deliberately not sorted order.
FILES = (('patches/0002-b.patch', b'b\n'), ('patches/0001-a.patch', b'a\n'))


def load():
    spec = importlib.util.spec_from_file_location('lock_patches', VENUS / 'lock_patches.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LockPatchesTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / 'patches').mkdir()
        for name, data in FILES:
            (self.root / name).write_bytes(data)
        entries = [{'file': n, 'sha256': hashlib.sha256(d).hexdigest()} for n, d in FILES]
        (self.root / 'sources.lock.json').write_text(json.dumps({'patches': entries}))

    def fails_with(self, message):
        with self.assertRaises(ValueError) as caught:
            self.mod.verified_patches(self.root)
        self.assertEqual(str(caught.exception), message)

    def test_returns_listed_patches_in_lock_order(self):
        self.assertEqual(self.mod.verified_patches(self.root),
                         [self.root / 'patches/0002-b.patch', self.root / 'patches/0001-a.patch'])

    def test_hash_mismatch_is_refused(self):
        (self.root / 'patches/0001-a.patch').write_bytes(b'changed\n')
        self.fails_with('hash mismatch: patches/0001-a.patch')

    def test_missing_listed_patch_is_refused(self):
        (self.root / 'patches/0001-a.patch').unlink()
        self.fails_with('missing patch: patches/0001-a.patch')

    def test_unlisted_patch_is_refused(self):
        (self.root / 'patches/0003-extra.patch').write_bytes(b'x\n')
        self.fails_with('unlisted patch: patches/0003-extra.patch')

    def test_other_files_in_patches_are_ignored(self):
        (self.root / 'patches/README.txt').write_bytes(b'notes\n')
        self.assertEqual(len(self.mod.verified_patches(self.root)), 2)

    def test_main_prints_one_posix_path_per_line(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.mod.main([str(self.root)])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), ''.join(
            (self.root / n).as_posix() + '\n' for n, _ in FILES))
        self.assertEqual(err.getvalue(), '')

    def test_main_prints_nothing_to_stdout_on_failure(self):
        (self.root / 'patches/0003-extra.patch').write_bytes(b'x\n')
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.mod.main([str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), 'lock_patches: unlisted patch: patches/0003-extra.patch\n')

    def test_current_tree_lists_all_patches_in_lock_order(self):
        names = [p.name for p in self.mod.verified_patches(VENUS)]
        self.assertEqual(len(names), 8)
        self.assertEqual(names, sorted(names))
        self.assertTrue(names[0].startswith('0001-') and names[-1].startswith('0008-'))


if __name__ == '__main__':
    unittest.main()
