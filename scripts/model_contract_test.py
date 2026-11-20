#!/usr/bin/env python3
"""Run one model's command-contract tests against the exact Forge CI package."""

from __future__ import annotations

import os

from forge_example import dependency_wheel, run_contract_tests


def item_slug() -> str:
    """Return the model item selected by CAD-CI."""

    value = os.environ.get("CAD_CI_ITEM", "").strip()
    if not value:
        raise RuntimeError("CAD_CI_ITEM is required")
    return value


def main() -> int:
    """Run the selected model's contract tests with the dependency wheel."""

    run_contract_tests(item_slug(), dependency_wheel())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
