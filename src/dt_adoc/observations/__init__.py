"""Observation positioning: where inside a simulated phase an experiment looked.

Deliberately separate from ``dt_adoc.simulation`` (which executes protocols) and
from ``dt_adoc.calibration`` (which scores them). This package neither runs
MaBoSS nor decides whether a candidate is retained: it declares, validates and
reads observation positions, and reports how much a verdict depends on where
those positions were placed.
"""
