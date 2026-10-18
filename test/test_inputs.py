"""Unit test for input lookup. Run: python test/test_inputs.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import ziti_hook  # noqa: E402


class InpTest(unittest.TestCase):
    def setUp(self):
        for k in [k for k in os.environ if k.startswith("INPUT_")]:
            del os.environ[k]

    def test_hyphen_form_from_github(self):
        os.environ["INPUT_ZITI-IDENTITY"] = " abc "
        self.assertEqual(ziti_hook.inp("ziti-identity"), "abc")

    def test_underscore_form(self):
        os.environ["INPUT_ZITI_IDENTITY"] = "abc"
        self.assertEqual(ziti_hook.inp("ziti-identity"), "abc")

    def test_hyphen_wins_over_underscore(self):
        os.environ["INPUT_SECRET-HEADER"] = "X-A"
        os.environ["INPUT_SECRET_HEADER"] = "X-B"
        self.assertEqual(ziti_hook.inp("secret-header"), "X-A")

    def test_empty_hyphen_value_is_not_replaced_by_default(self):
        os.environ["INPUT_SECRET-HEADER"] = ""
        self.assertEqual(ziti_hook.inp("secret-header", "X-Default"), "")

    def test_default(self):
        self.assertEqual(ziti_hook.inp("content-type", "application/json"), "application/json")

    def test_plain_name(self):
        os.environ["INPUT_URL"] = "http://x/"
        self.assertEqual(ziti_hook.inp("url"), "http://x/")


if __name__ == "__main__":
    unittest.main()
