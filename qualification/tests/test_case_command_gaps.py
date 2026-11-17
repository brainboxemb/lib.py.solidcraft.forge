"""Focused Q2 command contracts for cases without their own test module."""
from pathlib import Path
import unittest
from scpf.runner import run_script
ROOT=Path(__file__).resolve().parents[2]
def commands(slug): return run_script(ROOT/"examples"/slug/"scpf"/"model.py")["commands"]

class MissingCaseCommandContractTests(unittest.TestCase):
    def test_anchored_holes_command_contract(self):
        rows=commands("anchored-holes")
        self.assertEqual([r["params"]["name"] for r in rows if r["command"]=="sketch.create"],["Base","Holes"])
        circles=[r["params"] for r in rows if r["command"]=="sketch.circle.center"]
        self.assertEqual(len(circles),2); self.assertTrue(all("spacing" in str(r["center"][1]) for r in circles))
        self.assertEqual(rows[-1]["command"],"solid.extrude"); self.assertEqual(rows[-1]["params"]["operation"],"cut"); self.assertEqual(rows[-1]["params"]["distance"],"thickness")

    def test_components_command_contract(self):
        rows=commands("components"); copies=[r["params"] for r in rows if r["command"]=="occurrence.copy"]
        self.assertEqual(copies,[{"component":"Block","translate":[40.0,0.0,0.0]}])
        self.assertFalse(any(r["command"].startswith("joint.") for r in rows)); self.assertFalse(any(r["command"]=="occurrence.move" for r in rows))

    def test_parametric_attach_command_contract(self):
        rows=commands("parametric-attach")
        p=next(r["params"] for r in rows if r["command"]=="parameters.add" and r["params"]["name"]=="gap"); self.assertEqual(p["expression"],"10 mm")
        j=next(r["params"] for r in rows if r["command"]=="joint.create"); self.assertEqual(j["type"],"rigid"); self.assertEqual(j["a"]["occurrence"],"$base"); self.assertEqual(j["b"]["occurrence"],"$block"); self.assertEqual(j["offset"],"gap")

    def test_parametric_offset_command_contract(self):
        rows=commands("parametric-offset")
        p=next(r["params"] for r in rows if r["command"]=="parameters.add" and r["params"]["name"]=="shift"); self.assertEqual(p["expression"],"5 mm")
        j=next(r["params"] for r in rows if r["command"]=="joint.create"); self.assertEqual(j["type"],"planar"); self.assertEqual(j["a"]["occurrence"],"$base"); self.assertEqual(j["b"]["occurrence"],"$marker"); self.assertEqual(j["values"],[0,"-(shift)",0.0])

    def test_parametric_anchor_command_contract(self):
        rows=commands("parametric-anchor")
        p=next(r["params"] for r in rows if r["command"]=="parameters.add" and r["params"]["name"]=="base_width"); self.assertEqual((p["expression"],p["unit"]),("40","mm"))
        box=next(r["params"] for r in rows if r["command"]=="solid.box" and r["params"]["body_name"]=="Base"); self.assertEqual(box["length"],"base_width")
        j=next(r["params"] for r in rows if r["command"]=="joint.create"); self.assertEqual(j["type"],"rigid"); self.assertEqual(j["a"],{"face":[20.0,0.0,5.0],"occurrence":"$base"}); self.assertEqual(j["b"],{"face":[-10.0,0.0,5.0],"occurrence":"$block"})

    def test_corner_anchor_command_contract(self):
        j=next(r["params"] for r in commands("corner-anchor") if r["command"]=="joint.create")
        self.assertEqual(j["type"],"rigid"); self.assertEqual(j["a"]["occurrence"],"$base"); self.assertEqual(j["a"]["corner"],[20.0,-15.0,20.0]); self.assertEqual(j["b"]["occurrence"],"$marker"); self.assertEqual(j["b"]["point"],[5.0,5.0,10.0])

    def test_xz_anchor_command_contract(self):
        rows=commands("xz-anchor"); sketch=next(r["params"] for r in rows if r["command"]=="sketch.create"); self.assertEqual(sketch,{"plane":"XZ","name":"Profile"})
        joints=[r["params"] for r in rows if r["command"]=="joint.create"]; self.assertEqual(len(joints),2); self.assertEqual([j["a"]["corner"] for j in joints],[[20.0,0.0,20.0],[-20.0,0.0,20.0]]); self.assertEqual([j["b"]["occurrence"] for j in joints],["$rightmarker","$leftmarker"])

    def test_bracket_command_contract(self):
        rows=commands("bracket"); sketch=next(r["params"] for r in rows if r["command"]=="sketch.create"); polygon=next(r["params"] for r in rows if r["command"]=="sketch.line"); extrude=next(r["params"] for r in rows if r["command"]=="solid.extrude")
        self.assertEqual(sketch,{"plane":"XZ","name":"Profile"}); self.assertTrue(polygon["closed"]); self.assertEqual(len(polygon["points"]),6); self.assertEqual(extrude["distance"],"width"); self.assertEqual(extrude["direction"],"symmetric")
if __name__=="__main__": unittest.main()
