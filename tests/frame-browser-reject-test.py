"""Locked tests for the invalid-mode check in tests/frame-browser-test.sh.

Each case copies the test script and the frame-browser script into a sandbox,
optionally mutates the frame-browser script, and runs the test there.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'system_files/usr/local/libexec/stearlight/frame-browser'
REJECT = ("*) echo 'Expected browser GPU mode 0 or 1.' >&2; exit 1;; esac")


def run_test(mutate=None):
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / 'tests').mkdir()
        shutil.copy(ROOT / 'tests/frame-browser-test.sh', tmp / 'tests/frame-browser-test.sh')
        (tmp / SCRIPT).parent.mkdir(parents=True)
        text = (ROOT / SCRIPT).read_text()
        if mutate:
            text = mutate(text)
        (tmp / SCRIPT).write_text(text)
        return subprocess.run(['sh', str(tmp / 'tests/frame-browser-test.sh')],
                              capture_output=True, text=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def replace_once(old, new):
    def mutate(text):
        assert text.count(old) == 1, 'mutation anchor not found exactly once'
        return text.replace(old, new)
    return mutate


class ModeTwoRejection(unittest.TestCase):
    def test_real_script_passes(self):
        r = run_test()
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_crash_on_mode_two_fails(self):
        r = run_test(replace_once(REJECT, "*) echo 'internal error' >&2; exit 3;; esac"))
        self.assertNotEqual(r.returncode, 0)

    def test_wrong_rejection_message_fails(self):
        r = run_test(replace_once(REJECT, "*) echo 'Rejected.' >&2; exit 1;; esac"))
        self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
