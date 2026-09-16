#!/usr/bin/env python3
"""Zeigt fehlende Pflichtentscheidungen eines plan.json, ohne einen Container zu bauen."""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from lib.tracking_plan import missing_requirements  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("plan")
a = ap.parse_args()
plan = json.load(open(a.plan, encoding="utf-8"))
missing = missing_requirements(plan)
if missing:
    print(json.dumps({"complete": False, "missing": missing}, ensure_ascii=False, indent=2))
    sys.exit(2)
print(json.dumps({"complete": True, "missing": []}, ensure_ascii=False, indent=2))
