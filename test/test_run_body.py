"""Unit test for payload-mode run. Run: python test/test_run_body.py"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import ziti_hook  # noqa: E402

CTX = {
    "GITHUB_REPOSITORY": "dovholuknf/atrium",
    "GITHUB_RUN_ID": "39088705386",
    "GITHUB_RUN_ATTEMPT": "2",
    "GITHUB_WORKFLOW": "ci",
    "GITHUB_WORKFLOW_REF": "dovholuknf/atrium/.github/workflows/ci.yml@refs/heads/main",
    "GITHUB_REF_NAME": "main",
    "GITHUB_SHA": "abc123",
    "GITHUB_EVENT_NAME": "push",
    "GITHUB_SERVER_URL": "https://github.com",
}


class RunBodyTest(unittest.TestCase):
    def setUp(self):
        for k in [k for k in os.environ if k.startswith(("INPUT_", "GITHUB_"))]:
            del os.environ[k]
        os.environ.update(CTX)

    def test_shape(self):
        run = ziti_hook.build_run_body("failure")["workflow_run"]
        self.assertEqual(run["id"], 39088705386)
        self.assertEqual(run["run_attempt"], 2)
        self.assertEqual(run["path"], ".github/workflows/ci.yml")
        self.assertEqual(run["head_branch"], "main")
        self.assertEqual(run["head_sha"], "abc123")
        self.assertEqual(run["conclusion"], "failure")
        self.assertEqual(run["html_url"], "https://github.com/dovholuknf/atrium/actions/runs/39088705386")

    def test_head_ref_wins_for_pull_requests(self):
        os.environ["GITHUB_HEAD_REF"] = "feature"
        self.assertEqual(ziti_hook.build_run_body("failure")["workflow_run"]["head_branch"], "feature")

    def test_pull_request_head_sha(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"pull_request": {"head": {"sha": "deadbeef"}}}, f)
        os.environ.update(GITHUB_EVENT_NAME="pull_request", GITHUB_EVENT_PATH=f.name)
        self.assertEqual(ziti_hook.build_run_body("failure")["workflow_run"]["head_sha"], "deadbeef")
        os.remove(f.name)

    def test_bad_conclusion_exits(self):
        with self.assertRaises(SystemExit):
            ziti_hook.build_run_body("boom")

    def test_missing_run_id_exits(self):
        del os.environ["GITHUB_RUN_ID"]
        with self.assertRaises(SystemExit):
            ziti_hook.build_run_body("failure")

    def test_mode_run_through_build_payload(self):
        os.environ.update({"INPUT_PAYLOAD-MODE": "run", "INPUT_CONCLUSION": "cancelled"})
        body, ctype = ziti_hook.build_payload()
        self.assertEqual(ctype, "application/json")
        self.assertEqual(json.loads(body)["workflow_run"]["conclusion"], "cancelled")

    def test_explicit_payload_beats_mode(self):
        os.environ.update({"INPUT_PAYLOAD-MODE": "run", "INPUT_PAYLOAD": '{"a":1}'})
        self.assertEqual(ziti_hook.build_payload()[0], b'{"a":1}')


if __name__ == "__main__":
    unittest.main()
