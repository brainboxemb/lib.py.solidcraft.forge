"""Tests migrated from the former test_models.py catch-all."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from scpf.compiler import ModelError
from scpf.runner import run_script
from scpf import Sketch

ROOT = Path(__file__).resolve().parents[2]

class ModelAuthoring(unittest.TestCase):
    def test_every_public_core_api_name_is_available_to_model_scripts(self):
        import scpf
        from scpf import core
        from scpf import runner

        source = runner.__file__
        runner_text = Path(source).read_text(encoding="utf-8")
        public_core_names = {
            name
            for name in scpf.__all__
            if hasattr(core, name)
        }
        missing = sorted(
            name
            for name in public_core_names
            if f'"{name}": core.{name}' not in runner_text
        )
        self.assertEqual(
            missing,
            [],
            "public core API missing from run_script authoring context",
        )


    def test_model_imports_shared_components_when_run_from_nested_directory(self):
        """The CLI accepts 'model.py' while cwd is models/<name>/scpf."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            components = root / "models" / "components"
            components.mkdir(parents=True)
            (components / "tiny.py").write_text(
                "from scpf.core import Box\n"
                "class TinyPanel:\n"
                "    def build(self):\n"
                "        return Box(20, 10, 2)\n",
                encoding="utf-8",
            )
            model_dir = root / "models" / "screen" / "scpf"
            model_dir.mkdir(parents=True)
            (model_dir / "model.py").write_text(
                "from scpf.runner import component\n"
                "from models.components.tiny import TinyPanel\n"
                "class Screen:\n"
                "    def build(self):\n"
                "        return component(TinyPanel)()\n"
                "Screen()\n",
                encoding="utf-8",
            )
            original_cwd = Path.cwd()
            original_paths = sys.path[:]
            try:
                os.chdir(model_dir)
                command_plan = run_script("model.py")
                names = [row["command"] for row in command_plan["commands"]]
                self.assertEqual(names.count("component.create"), 1)
                self.assertIn("solid.box", names)
                self.assertEqual(sys.path, original_paths)
            finally:
                os.chdir(original_cwd)
                for module in ("models.components.tiny", "models.components", "models"):
                    sys.modules.pop(module, None)

    def test_removed_aliases_are_not_exposed(self):
        import scpf
        for name in (
            "Rectangle", "Circle", "Polygon", "Cube",
            "Box3D", "Cylinder3D", "Sphere3D",
            "History", "behavior",
        ):
            self.assertFalse(hasattr(scpf, name), name)

    def test_plain_model_class_fields_become_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class Cuboid:\n"
                "    length = 80.0\n"
                "    width = 50.0\n"
                "    height = 30.0\n"
                "    def build(self):\n"
                "        Box(self.length, self.width, self.height)\n"
                "Cuboid(width=60.0)\n"
            )
            generated = run_script(file)
        self.assertEqual(
            [c["params"]["name"] for c in generated["commands"][:3]],
            ["length", "width", "height"],
        )
        self.assertEqual(
            [c["params"]["expression"] for c in generated["commands"][:3]],
            ["80", "60", "30"],
        )

    def test_plain_model_class_accepts_positional_overrides_in_field_order(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class Cuboid:\n"
                "    length = 80.0\n"
                "    width = 50.0\n"
                "    height = 30.0\n"
                "    def build(self):\n"
                "        Box(self.length, self.width, self.height)\n"
                "Cuboid(100.0, 70.0)\n"
            )
            generated = run_script(file)
        self.assertEqual(
            [c["params"]["expression"] for c in generated["commands"][:3]],
            ["100", "70", "30"],
        )

    def test_frozen_dataclass_build_with_implicit_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "@dataclass(frozen=True)\n"
                "class Cuboid:\n"
                "    size: float = 50\n"
                "    def __post_init__(self):\n"
                "        assert self.size > 0\n"
                "    def build(self):\n"
                "        Box(self.size, self.size, self.size).move(x=10)\n"
                "Cuboid(80)\n"
            )
            generated = run_script(file)
        self.assertEqual(generated["commands"][0]["params"]["name"], "size")
        self.assertEqual(generated["commands"][0]["params"]["expression"], "80")
        self.assertEqual(generated["commands"][1]["params"]["center"], [10, 0, 0])

    def test_dataclass_constructor_validates_before_symbolic_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "@dataclass\n"
                "class Cuboid:\n"
                "    size: float = 50\n"
                "    def __post_init__(self):\n"
                "        assert self.size > 0\n"
                "    def build(self):\n"
                "        Box(self.size, self.size, self.size)\n"
                "Cuboid(-5)\n"
            )
            with self.assertRaises(AssertionError):
                run_script(file)

    def test_dataclass_requires_build_method(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "@dataclass\n"
                "class Cuboid:\n"
                "    size: float = 50\n"
                "Cuboid()\n"
            )
            with self.assertRaisesRegex(TypeError, "must define build"):
                run_script(file)

    def test_dataclass_build_must_finish_with_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "@dataclass\n"
                "class Cuboid:\n"
                "    size: float = 50\n"
                "    def build(self):\n"
                "        body = Box(self.size, self.size, self.size)\n"
                "Cuboid()\n"
            )
            with self.assertRaisesRegex(TypeError, "finish with a Shape"):
                run_script(file)

    def test_arguments_are_editable_without_decorators(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "def CsgCube(size=50.0):\n"
                "    return Sphere(size / 1.5) & Box(size, size, size)\n"
                "CsgCube(60.0)\n"
            )
            generated = run_script(file)
        self.assertEqual(generated["commands"][0]["params"]["expression"], "60")
        self.assertEqual(generated["commands"][1]["params"]["radius"], "size / 1.5")

    def test_model_function_implicit_shape_expression(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "def Cuboid(size=50):\n"
                "    body = Box(size, size, size)\n"
                "    body.move(x=10)\n"
                "Cuboid()\n"
            )
            generated = run_script(file)
        self.assertEqual(generated["commands"][1]["params"]["center"], [10, 0, 0])

    def test_assignment_only_function_must_still_explicitly_return(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "def Cuboid(size=50):\n"
                "    body = Box(size, size, size)\n"
                "Cuboid()\n"
            )
            with self.assertRaises(TypeError):
                run_script(file)

    def test_function_model_still_requires_explicit_final_call(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "def CubeModel(size=50):\n"
                "    return Box(size, size, size)\n"
            )
            with self.assertRaisesRegex(
                SyntaxError,
                "exactly one public class with build",
            ):
                run_script(file)

    def test_single_public_model_class_runs_directly_without_launcher_call(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "corner_bracket.py"
            file.write_text(
                "from scpf.core import Box\n"
                "class CornerBracket:\n"
                "    width = 24.0\n"
                "    def build(self):\n"
                "        return Box(self.width, 40, 40)\n",
                encoding="utf-8",
            )
            generated = run_script(file)

        self.assertEqual(
            [
                command["params"]["name"]
                for command in generated["commands"]
                if command["command"] == "parameters.add"
            ],
            ["width"],
        )
        self.assertTrue(
            any(command["command"] == "solid.box"
                for command in generated["commands"])
        )

    def test_direct_root_refuses_to_guess_between_public_model_classes(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "models.py"
            file.write_text(
                "class First:\n"
                "    def build(self):\n"
                "        return Box(10, 10, 10)\n"
                "class Second:\n"
                "    def build(self):\n"
                "        return Box(20, 20, 20)\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                SyntaxError,
                "candidates: First, Second",
            ):
                run_script(file)

    def test_imported_class_can_be_the_root_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "shared.py").write_text(
                "from scpf.core import Box\n"
                "class Bracket:\n"
                "    width = 24.0\n"
                "    _x_position = 0.0\n"
                "    def build(self):\n"
                "        return Box(self.width, 10, 10)\n",
                encoding="utf-8",
            )
            model = root / "model.py"
            model.write_text(
                "from shared import Bracket\n"
                "Bracket()\n",
                encoding="utf-8",
            )
            generated = run_script(model)

        names = [
            command["params"]["name"]
            for command in generated["commands"]
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(names, ["width"])
        self.assertNotIn("_x_position", names)

    def test_model_local_imports_do_not_create_pycache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "helper.py").write_text(
                "from scpf.core import Box\n"
                "class HelperBox:\n"
                "    size = 10.0\n"
                "    def build(self):\n"
                "        return Box(self.size, self.size, self.size)\n"
            )
            model = root / "model.py"
            model.write_text(
                "from helper import HelperBox\n"
                "class Wrapper:\n"
                "    size = 20.0\n"
                "    def build(self):\n"
                "        return Box(self.size, self.size, self.size)\n"
                "Wrapper()\n"
            )
            run_script(model)
            self.assertFalse((root / "__pycache__").exists())

    def test_plain_model_subclass_inherits_parameters_and_build(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class Board:\n"
                "    width = 100.0\n"
                "    depth = 40.0\n"
                "    thickness = 12.0\n"
                "    corner_radius = 4.0\n"
                "    def build(self):\n"
                "        return Box(self.width, self.depth, self.thickness).fillet(\n"
                "            self.corner_radius, edges=Edges.VERTICAL)\n"
                "class BottomBoard(Board):\n"
                "    pass\n"
                "BottomBoard(width=868.0, depth=100.0)\n"
            )
            generated = run_script(file)
        params = [c["params"] for c in generated["commands"]
                  if c["command"] == "parameters.add"]
        self.assertEqual([p["name"] for p in params],
                         ["width", "depth", "thickness", "corner_radius"])
        self.assertEqual([p["expression"] for p in params],
                         ["868", "100", "12", "4"])
        fillet = next(c for c in generated["commands"]
                      if c["command"] == "solid.fillet")
        self.assertEqual(fillet["params"]["radius"], "corner_radius")

    def test_parameter_naming_distinguishes_model_build_and_constant_values(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class Display:\n"
                "    opening_width = 844.0\n"
                "    panel_count = 5\n"
                "    _panel_pitch = 160.0\n"
                "    PANEL_DEPTH = 14.5\n"
                "    def build(self):\n"
                "        count = int(pv(self.panel_count))\n"
                "        assert count == 5\n"
                "        return Box(self.opening_width, self._panel_pitch, self.PANEL_DEPTH)\n"
                "Display()\n",
                encoding="utf-8",
            )
            with self.assertWarnsRegex(
                UserWarning,
                "parameter 'panel_count' has no native SolidCraft dependency",
            ):
                generated = run_script(file)

        names = [
            command["params"]["name"]
            for command in generated["commands"]
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(names, ["opening_width"])
        self.assertNotIn("_panel_pitch", names)
        self.assertNotIn("PANEL_DEPTH", names)

    def test_partial_pv_flattening_warns_even_with_native_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "partial.py"
            file.write_text(
                "class Partial:\n"
                "    width = 40.0\n"
                "    def build(self):\n"
                "        fixed_depth = pv(self.width) / 2\n"
                "        return Box(self.width, fixed_depth, 5)\n"
                "Partial()\n",
                encoding="utf-8",
            )
            with self.assertWarnsRegex(
                UserWarning,
                "parameter 'width' remains a native dependency, but pv\\(\\) also consumes",
            ):
                generated = run_script(file)

        box = next(
            command["params"]
            for command in generated["commands"]
            if command["command"] == "solid.box"
        )
        self.assertEqual(box["length"], "width")
        self.assertEqual(box["width"], 20.0)

    def test_root_assembly_uses_same_parameter_dependency_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "assembly_warning.py"
            file.write_text(
                "@component\n"
                "class Panel:\n"
                "    def build(self):\n"
                "        return Box(20, 10, 2)\n"
                "@assembly\n"
                "class Display:\n"
                "    offset = 30.0\n"
                "    count = 2\n"
                "    def build(self):\n"
                "        count = int(pv(self.count))\n"
                "        assert count == 2\n"
                "        first = Panel()\n"
                "        second = first.copy(placement=Placement(x=self.offset))\n"
                "        return first + second\n"
                "Display()\n",
                encoding="utf-8",
            )
            import warnings
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                generated = run_script(file)

        model_warnings = [
            str(item.message)
            for item in caught
            if "Display parameter" in str(item.message)
        ]
        self.assertEqual(len(model_warnings), 1)
        self.assertIn("parameter 'count' has no native SolidCraft dependency", model_warnings[0])
        self.assertNotIn("offset", model_warnings[0])

        move = next(
            command["params"]
            for command in generated["commands"]
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["translate"][0], "offset")

    def test_nested_component_pv_does_not_mark_same_named_parent_parameter(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "nested_pv.py"
            file.write_text(
                "@component\n"
                "class Child:\n"
                "    width = 40.0\n"
                "    def build(self):\n"
                "        fixed = pv(self.width)\n"
                "        return Box(fixed, 10, 2)\n"
                "class Display:\n"
                "    width = 40.0\n"
                "    def build(self):\n"
                "        first = Child()\n"
                "        second = first.copy(placement=Placement(x=self.width))\n"
                "        return first + second\n"
                "Display()\n",
                encoding="utf-8",
            )
            import warnings
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                run_script(file)

        self.assertFalse(
            any(
                "Display parameter 'width'" in str(item.message)
                for item in caught
            )
        )

    def test_public_parameter_kept_in_native_geometry_does_not_warn(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class Display:\n"
                "    opening_width = 844.0\n"
                "    def build(self):\n"
                "        return Box(self.opening_width, 100, 20)\n"
                "Display()\n",
                encoding="utf-8",
            )
            # No ModelParameterWarning should be emitted.
            import warnings
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                generated = run_script(file)

        self.assertFalse(
            any("no native SolidCraft dependency" in str(item.message)
                for item in caught)
        )
        self.assertEqual(
            [c["params"]["name"] for c in generated["commands"]
             if c["command"] == "parameters.add"],
            ["opening_width"],
        )



if __name__ == "__main__":
    unittest.main()
