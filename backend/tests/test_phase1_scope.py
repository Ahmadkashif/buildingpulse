"""Phase-scope guards for Phase 1.

These tests assert what Phase 1 *has not done* — they fail if a later phase's
concern (model loading, data ingestion, artifact persistence) leaks in early.

Static source checks, not runtime. If Phase N adds an import, these tests
flag it before the code runs.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"
BACKEND_DIR = APP_DIR.parent

FORBIDDEN_IMPORTS = {"pandas", "sklearn", "joblib", "numpy"}
FORBIDDEN_STRINGS = ["dataset.csv", "model.pkl", "artifacts/"]


def _app_python_files() -> list[Path]:
    return sorted(APP_DIR.rglob("*.py"))


def _top_level_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


class TestForbiddenImports:
    @pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_IMPORTS))
    def test_no_app_file_imports(self, forbidden: str) -> None:
        offenders: list[str] = []
        for path in _app_python_files():
            imports = _top_level_imports(path.read_text())
            if forbidden in imports:
                offenders.append(str(path.relative_to(BACKEND_DIR)))
        assert not offenders, (
            f"Phase 1 must not import {forbidden!r}; found in: {offenders}"
        )


class TestForbiddenStrings:
    @pytest.mark.parametrize("forbidden", FORBIDDEN_STRINGS)
    def test_no_app_file_references(self, forbidden: str) -> None:
        offenders: list[str] = []
        for path in _app_python_files():
            if forbidden in path.read_text():
                offenders.append(str(path.relative_to(BACKEND_DIR)))
        assert not offenders, (
            f"Phase 1 must not reference {forbidden!r}; found in: {offenders}"
        )


class TestArtifactsDirectoryAbsent:
    def test_artifacts_directory_does_not_exist(self) -> None:
        artifacts = BACKEND_DIR / "artifacts"
        assert not artifacts.exists(), (
            "backend/artifacts/ is Phase 3+ output; it must not exist at Phase 1."
        )
