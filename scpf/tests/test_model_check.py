"""Model-authoring checks for issue #213."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from scpf.__main__ import main
from scpf.runner import run_script


class ModelCheckTests(unittest.TestCase):
    def _script(self, directory, source):
        path = Path(directory) / "model.py"
        path.write_text(source, encoding="utf-8")
        return path

    def test_check_builds_and_compiles_without_native_solidcraft(self):
        with tempfile.TemporaryDirectory() as directory:
            script = self._script(
                directory,
                "class Good:\n"
                "    width = 40.0\n"
                "    def build(self):\n"
                "        return Box(self.width, 20, 5)\n"
                "Good()\n",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = main(["check", str(script)])

        self.assertEqual(result, 0)
        self.assertIn("SCPF check PASS", stdout.getvalue())
        self.assertIn("SolidCraft commands", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_check_returns_nonzero_for_model_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            script = self._script(
                directory,
                "class Bad:\n"
                "    hole_columns = 2\n"
                "    def build(self):\n"
                "        for column in range(self.hole_columns):\n"
                "            pass\n"
                "        return Box(20, 20, 5)\n"
                "Bad()\n",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    main(["check", str(script)])

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("editable CAD parameter", stderr.getvalue())
        self.assertIn("_hole_columns", stderr.getvalue())

    def test_shape_group_explains_component_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            script = self._script(
                directory,
                "class Bad:\n"
                "    def build(self):\n"
                "        return Box(20, 20, 5).group('Parts')\n"
                "Bad()\n",
            )
            with self.assertRaisesRegex(
                AttributeError, "component occurrences or Assemblies"
            ):
                run_script(script)

    def test_material_assigned_shapes_explain_physical_part_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            script = self._script(
                directory,
                "class Bad:\n"
                "    def build(self):\n"
                "        left = Box(20, 20, 5).with_material(\n"
                "            'Wood', density_g_cm3=0.7)\n"
                "        right = Box(20, 20, 5).move(x=30).with_material(\n"
                "            'Metal', density_g_cm3=7.8)\n"
                "        return left + right\n"
                "Bad()\n",
            )
            with self.assertRaisesRegex(
                TypeError, "separate physical parts or different materials"
            ):
                run_script(script)


if __name__ == "__main__":
    unittest.main()
