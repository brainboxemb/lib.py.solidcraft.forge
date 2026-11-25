from types import SimpleNamespace
import unittest

from cad_library_ci.__main__ import qualification_plan


class BuildPlanTests(unittest.TestCase):
    def test_records_library_qualification_explicitly(self):
        models = (
            SimpleNamespace(
                id="example",
                primary="scpf",
                implementations=(SimpleNamespace(id="scpf"),),
                purposes=("example", "verification"),
            ),
        )
        plan = qualification_plan(
            models=models,
            selected=models,
            source_sha="a" * 40,
            full=True,
            library=True,
        )
        self.assertEqual(plan["schema"], 2)
        self.assertTrue(plan["library"])
        self.assertTrue(plan["full"])
        self.assertEqual(plan["active"], ["example"])
        self.assertEqual(plan["selected"], ["example"])
        self.assertEqual(plan["models"][0]["implementations"], ["scpf"])


if __name__ == "__main__":
    unittest.main()
