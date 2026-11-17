#!/usr/bin/env python3
"""Run explicit case-specific Q1 or Q2 unittest evidence."""
from __future__ import annotations
import argparse, csv, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qualification.case_evidence import evidence_for, validate_case_evidence
from qualification.cases import supported_qualification_cases

_RAN = re.compile(r"Ran\s+(\d+)\s+tests?")

def _run_target(target):
    path = ROOT / target["file"]
    if target["file"].startswith("scpf/tests/"):
        command = [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT/"scpf/tests"), "-p", path.name, "-k", target["test"], "-v"]
    else:
        command = [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT/"qualification/tests"), "-t", str(ROOT), "-p", path.name, "-k", target["test"], "-v"]
    env = dict(os.environ); env.pop("PYTHONPATH", None)
    completed = subprocess.run(command, cwd=Path.cwd(), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    match = _RAN.search(completed.stdout)
    count = int(match.group(1)) if match else 0
    return command, completed.stdout, count, completed.returncode == 0 and count > 0

def run(level, out):
    validate_case_evidence()
    (out/"case-evidence"/level).mkdir(parents=True, exist_ok=True)
    rows, failures = [], []
    for case in supported_qualification_cases():
        slug = case["slug"]; targets = list(evidence_for(slug, level)); log=[]; passed=True
        for target in targets:
            command, output, count, ok = _run_target(target)
            log += ["$ "+" ".join(command), output.rstrip(), f"matched_tests={count} status={'PASS' if ok else 'FAIL'}"]
            passed = passed and ok
        evidence = f"case-evidence/{level}/{slug}.txt"
        (out/evidence).write_text("\n\n".join(log)+"\n", encoding="utf-8")
        status = "PASS" if passed else "FAIL"
        rows.append({"case":slug,"status":status,"tests":json.dumps(targets,separators=(",",":")),"evidence":evidence})
        if not passed: failures.append(slug)
    with (out/f"{level}-case-evidence.tsv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=("case","status","tests","evidence"),delimiter="\t"); writer.writeheader(); writer.writerows(rows)
    if failures:
        print(f"{level.upper()} case evidence failed: {', '.join(failures)}", file=sys.stderr); return 1
    print(f"{level.upper()} case evidence PASS: {len(rows)} cases"); return 0

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--level",choices=("q1","q2"),required=True); parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args(); args.out.mkdir(parents=True,exist_ok=True); return run(args.level,args.out)
if __name__=="__main__": raise SystemExit(main())
