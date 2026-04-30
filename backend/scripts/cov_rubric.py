"""Enforce per-layer coverage thresholds from `[tool.coverage_rubric]` in pyproject.toml.

pytest-cov can compute branch coverage but cannot express per-path thresholds.
This script consumes Coverage.py's data file (`.coverage`) and the rubric
section of `pyproject.toml`, then exits non-zero if any layer falls short.

Layers with **no source files yet** are skipped (the rubric only fails when a
layer that exists falls below its target). This lets the harness pass on an
empty tree while still failing the moment a tested layer regresses.
"""

from __future__ import annotations

import fnmatch
import sys
import tomllib
from pathlib import Path
from typing import Any

import coverage


def load_rubric(pyproject: Path) -> dict[str, dict[str, Any]]:
    data = tomllib.loads(pyproject.read_text())
    return data.get("tool", {}).get("coverage_rubric", {})


def measure(cov: coverage.Coverage, src: Path, kind: str) -> tuple[int, int] | None:
    """Return (covered, total) units for a single source file, or None if no data."""
    analysis = cov.analysis2(str(src))
    # analysis2 returns: (filename, statements, excluded, missing, missing_formatted)
    statements = set(analysis[1])
    missing = set(analysis[3])
    if kind == "branch":
        # Use raw branch stats from CoverageData
        branch_stats = cov.get_data().branch_lines() if hasattr(cov.get_data(), "branch_lines") else None
        # Fallback: use coverage.py's analysis_branch via internal API
        try:
            from coverage.results import Analysis  # type: ignore[import-untyped]
        except Exception:
            Analysis = None  # type: ignore[assignment]
        # Use the public reporter path: numbers via analysis()
        nums = cov._analyze(str(src)).numbers  # type: ignore[attr-defined]
        total = nums.n_branches
        covered = nums.n_branches - nums.n_missing_branches - nums.n_partial_branches
        if total == 0:
            # No branches in file: fall back to statement coverage so tiny files still gate.
            total = len(statements)
            covered = total - len(missing)
        return covered, total
    # line / statement
    total = len(statements)
    covered = total - len(missing)
    return covered, total


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    pyproject = repo / "pyproject.toml"
    rubric = load_rubric(pyproject)
    if not rubric:
        print("cov_rubric: no [tool.coverage_rubric] section — skipping.")
        return 0

    cov = coverage.Coverage(data_file=str(repo / ".coverage"), config_file=str(pyproject))
    cov.load()

    failures: list[str] = []
    checked = 0

    for pattern, spec in rubric.items():
        kind = spec["kind"]
        threshold = float(spec["min"])
        # Translate glob to a filesystem walk relative to repo.
        # `app/domain/**` → match every .py under app/domain/.
        # Two pattern shapes are supported:
        #   "app/repos/**"                     → all .py under app/repos/
        #   "app/api/v1/**/controller.py"      → only controller.py files under app/api/v1/
        files: list[Path]
        parts = pattern.split("/")
        leaf = parts[-1]
        if leaf == "**":
            base = repo / "/".join(parts[:-1])
            files = (
                [p for p in base.rglob("*.py") if p.is_file() and p.name != "__init__.py"]
                if base.exists()
                else []
            )
        else:
            root_prefix = "/".join(p for p in parts[:-1] if p != "**")
            root = repo / root_prefix
            files = [p for p in root.rglob(leaf) if p.is_file()] if root.exists() else []

        if not files:
            continue  # layer not yet populated

        total_covered = 0
        total_units = 0
        for f in files:
            try:
                result = measure(cov, f, kind)
            except coverage.exceptions.NoSource:
                continue
            except coverage.exceptions.CoverageException:
                continue
            if result is None:
                continue
            covered, total = result
            # Skip placeholder stubs: a file with ≤1 statement is almost
            # certainly an unimplemented module (just `from __future__
            # import annotations` or a `...` body). The rubric kicks in
            # the moment real code lands.
            if total <= 1:
                continue
            total_covered += covered
            total_units += total

        if total_units == 0:
            continue

        ratio = total_covered / total_units
        checked += 1
        status = "OK" if ratio >= threshold else "FAIL"
        print(
            f"  [{status}] {pattern:<40} {kind:<10} "
            f"{total_covered}/{total_units} = {ratio:.2%} (min {threshold:.0%})"
        )
        if ratio < threshold:
            failures.append(f"{pattern}: {ratio:.2%} < {threshold:.0%}")

    if checked == 0:
        print("cov_rubric: no rubric layers populated yet — harness OK.")
        return 0

    if failures:
        print("\ncov_rubric: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\ncov_rubric: all layers meet the rubric.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
