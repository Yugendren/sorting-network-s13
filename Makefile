SHELL := /bin/bash
PYTHON ?= python3

.PHONY: setup verify baseline-b0 baseline-b1 baseline-b2 baseline-b3 baseline-b4 baseline setup-method-instrumented setup-method-v1 method-e0 method-e1 method-e2-train method-e2-validate evidence-check report clean

setup:
	$(PYTHON) tools/setup_sources.py
	$(PYTHON) tools/setup_senso.py
	$(PYTHON) tools/setup_sortnetopt.py
	$(PYTHON) tools/fetch_harder_certificate.py

verify:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

baseline-b0:
	$(PYTHON) tools/b0_gate.py

baseline-b1:
	$(PYTHON) tools/b1_gate.py

baseline-b2:
	$(PYTHON) tools/b2_gate.py

baseline-b3:
	$(PYTHON) tools/b3_gate.py

baseline-b4:
	$(PYTHON) tools/b4_gate.py

baseline: baseline-b0 baseline-b1 baseline-b2 baseline-b3 baseline-b4

method-e0:
	$(PYTHON) tools/e0_method_gate.py

setup-method-instrumented:
	$(PYTHON) tools/setup_senso_instrumented.py

setup-method-v1:
	$(PYTHON) tools/setup_senso_mericanii_v1.py

method-e1:
	$(PYTHON) tools/e1_dataset_gate.py

method-e2-train:
	$(PYTHON) tools/e2_train_gate.py

method-e2-validate:
	$(PYTHON) tools/e2_validation_gate.py

evidence-check:
	$(PYTHON) tools/evidence_check.py

report:
	@report="$$(find evidence/b4 -mindepth 2 -maxdepth 2 -type f -name baseline-report.md 2>/dev/null | sort | tail -n 1)"; \
	  test -n "$$report" || { echo "No B4 baseline report exists." >&2; exit 2; }; \
	  sed -n '1,400p' "$$report"

clean:
	@echo "Scored evidence and external caches are intentionally never removed by make." >&2
