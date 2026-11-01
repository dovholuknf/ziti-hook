"""Unit test for fail-on-error. Run: python test/test_fail_on_error.py"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import ziti_hook  # noqa: E402


class FailOnErrorTest(unittest.TestCase):
    def setUp(self):
        for k in [k for k in os.environ if k.startswith("INPUT_")]:
            del os.environ[k]

    def test_default_propagates_exit(self):
        with mock.patch.object(ziti_hook, "run", side_effect=SystemExit("boom")):
            with self.assertRaises(SystemExit):
                ziti_hook.main()

    def test_default_propagates_exception(self):
        with mock.patch.object(ziti_hook, "run", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                ziti_hook.main()

    def test_false_swallows_exit_and_warns(self):
        os.environ["INPUT_FAIL-ON-ERROR"] = "false"
        with mock.patch.object(ziti_hook, "run", side_effect=SystemExit(1)), mock.patch("builtins.print") as p:
            ziti_hook.main()
        self.assertIn("::warning::", p.call_args[0][0])

    def test_false_swallows_exception_and_warns(self):
        os.environ["INPUT_FAIL_ON_ERROR"] = "False"
        with mock.patch.object(ziti_hook, "run", side_effect=OSError("no terminators")), mock.patch("builtins.print") as p:
            ziti_hook.main()
        self.assertIn("no terminators", p.call_args[0][0])

    def test_success_exit_is_untouched(self):
        os.environ["INPUT_FAIL-ON-ERROR"] = "false"
        with mock.patch.object(ziti_hook, "run", side_effect=SystemExit(0)):
            with self.assertRaises(SystemExit):
                ziti_hook.main()


if __name__ == "__main__":
    unittest.main()
