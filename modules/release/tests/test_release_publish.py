import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from cad_library_release import publish


SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


def not_found() -> HTTPError:
    return HTTPError("https://api.github.com", 404, "Not found", {}, None)


class ReleasePublishTests(unittest.TestCase):
    def test_create_annotated_tag_creates_tag_object_then_ref(self):
        base = "https://api.github.com/repos/owner/repo"
        with patch.object(publish, "_request", side_effect=[{"sha": SHA_C}, {}]) as request:
            publish._create_annotated_tag(base, "v1.2.3", SHA_A, "token")

        self.assertEqual(request.call_args_list[0].args[0], f"{base}/git/tags")
        self.assertEqual(
            request.call_args_list[0].kwargs["data"],
            {"tag": "v1.2.3", "message": "v1.2.3", "object": SHA_A, "type": "commit"},
        )
        self.assertEqual(
            request.call_args_list[1].kwargs["data"],
            {"ref": "refs/tags/v1.2.3", "sha": SHA_C},
        )

    def test_existing_exact_annotated_release_is_idempotent(self):
        annotated = {"type": "tag", "sha": SHA_C}
        with (
            patch.object(publish, "_tag_reference", return_value=annotated),
            patch.object(publish, "_tag_commit", return_value=SHA_A),
            patch.object(publish, "_request", side_effect=[
                {"object": {"type": "commit", "sha": SHA_A}},
                {"html_url": "https://example.test/releases/v1.2.3"},
            ]),
        ):
            result = publish.publish_exact_release("owner/repo", "1.2.3", SHA_A, "token")
        self.assertFalse(result.created)
        self.assertEqual(result.target_sha, SHA_A)

    def test_existing_lightweight_tag_is_rejected(self):
        lightweight = {"type": "commit", "sha": SHA_A}
        with (
            patch.object(publish, "_tag_reference", return_value=lightweight),
            patch.object(
                publish,
                "_request",
                return_value={"object": {"type": "commit", "sha": SHA_A}},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "not an annotated tag"):
                publish.publish_exact_release("owner/repo", "1.2.3", SHA_A, "token")

    def test_existing_annotated_tag_on_other_commit_fails_closed(self):
        annotated = {"type": "tag", "sha": SHA_C}
        with (
            patch.object(publish, "_tag_reference", return_value=annotated),
            patch.object(publish, "_tag_commit", return_value=SHA_B),
            patch.object(
                publish,
                "_request",
                return_value={"object": {"type": "commit", "sha": SHA_A}},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "refusing to relabel"):
                publish.publish_exact_release("owner/repo", "1.2.3", SHA_A, "token")

    def test_release_target_must_equal_stable_head(self):
        with patch.object(
            publish,
            "_request",
            return_value={"object": {"type": "commit", "sha": SHA_B}},
        ):
            with self.assertRaisesRegex(ValueError, "must equal main HEAD"):
                publish.publish_exact_release("owner/repo", "1.2.3", SHA_A, "token")

    def test_missing_release_creates_annotated_tag_then_release(self):
        annotated = {"type": "tag", "sha": SHA_C}
        with (
            patch.object(publish, "_tag_reference", side_effect=[None, annotated]),
            patch.object(publish, "_tag_commit", return_value=SHA_A),
            patch.object(publish, "_create_annotated_tag") as create_tag,
            patch.object(publish, "_request", side_effect=[
                {"object": {"type": "commit", "sha": SHA_A}},
                not_found(),
                {"html_url": "https://example.test/releases/v1.2.3"},
            ]) as request,
        ):
            result = publish.publish_exact_release(
                "owner/repo", "1.2.3", SHA_A, "token", notes="qualified notes\n"
            )

        self.assertTrue(result.created)
        create_tag.assert_called_once()
        post = request.call_args_list[2]
        self.assertEqual(post.kwargs["method"], "POST")
        self.assertEqual(post.kwargs["data"]["body"], "qualified notes\n")


if __name__ == "__main__":
    unittest.main()
