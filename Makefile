SHELL := /bin/bash
PYTHON ?= python3

.PHONY: setup verify baseline-b0 baseline-b1 baseline-b2 baseline-b3 baseline-b4 baseline evidence-check report clean

setup:
	$(PYTHON) tools/setup_sources.py

verify:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

baseline-b0:
	$(PYTHON) tools/b0_gate.py

baseline-b1:
	$(PYTHON) tools/b1_gate.py

baseline-b2:
	@echo "B2 is not established yet; run only after the B1 checkpoint." >&2
	@exit 2

baseline-b3:
	@echo "B3 is not established yet; run only after the B2 checkpoint." >&2
	@exit 2

baseline-b4:
	@echo "B4 is not established yet; run only after the B3 checkpoint." >&2
	@exit 2

baseline: baseline-b0 baseline-b1 baseline-b2 baseline-b3 baseline-b4

evidence-check:
	$(PYTHON) tools/evidence_check.py

report:
	@test -f evidence/reports/baseline-report.md || { echo "No B4 baseline report exists." >&2; exit 2; }
	@sed -n '1,240p' evidence/reports/baseline-report.md

clean:
	@echo "Scored evidence and external caches are intentionally never removed by make." >&2
