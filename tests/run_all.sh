#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1

for case_name in \
  test_launch \
  test_urlguard \
  test_bericht \
  test_builder \
  test_template \
  test_siteone \
  test_doctor \
  test_dokumentation \
  test_netzpolicy \
  test_skill_invocation \
  test_consent_logic \
  test_geo_agent_readiness \
  test_plan_completeness_gate \
  test_gtm_golden_master \
  test_reference_assets
do
  python3 -u tests/run_tests.py --case "$case_name"
done

printf '\nFull regression: 221/221 expected; all 15 isolated blocks passed.\n'
