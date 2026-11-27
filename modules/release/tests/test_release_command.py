import unittest

from cad_library_release.command import parse_release_command


class ReleaseCommandTests(unittest.TestCase):
    def test_parse_exact_release_command(self):
        version, sha = parse_release_command("/release v1.2.3 " + "a" * 40)
        self.assertEqual(version, "1.2.3")
        self.assertEqual(sha, "a" * 40)

    def test_reject_extra_missing_or_malformed_command_parts(self):
        invalid = (
            "/release",
            "/release 1.2.3 " + "a" * 40,
            "/release v1.2 " + "a" * 40,
            "/release v1.2.3 main",
            "/release v1.2.3 " + "a" * 40 + " extra",
            "/publish v1.2.3 " + "a" * 40,
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_release_command(value)


if __name__ == "__main__":
    unittest.main()
