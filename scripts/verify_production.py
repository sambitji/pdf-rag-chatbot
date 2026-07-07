"""Simple production-readiness verification script."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    checks = []
    checks.append(("requirements.txt exists", (ROOT / "requirements.txt").exists()))
    checks.append((".env exists", (ROOT / ".env").exists()))
    checks.append(("health endpoint module exists", (ROOT / "api" / "main.py").exists()))
    checks.append(("validator module exists", (ROOT / "utils" / "validators.py").exists()))
    checks.append(("tests exist", (ROOT / "tests").exists()))

    for name, passed in checks:
        print(f"[{'OK' if passed else 'FAIL'}] {name}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
