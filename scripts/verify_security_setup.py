#!/usr/bin/env python
"""Verify security setup and configuration."""
import re
import sys
from pathlib import Path


def check_pinned_dependencies() -> bool:
    """Verify all dependencies are pinned with == operator."""
    pyproject = Path("pyproject.toml").read_text()

    # Find all dependencies section
    dependencies_match = re.search(
        r'dependencies\s*=\s*\[([\s\S]*?)\]',
        pyproject,
        re.MULTILINE
    )

    if not dependencies_match:
        print("ERROR: Could not find dependencies section")
        return False

    deps_text = dependencies_match.group(1)

    # Check for >= or other operators
    if re.search(r'[<>!~]+=', deps_text) and '>=' in deps_text:
        bad_deps = re.findall(r'"([^"]+>=.*?)"', deps_text)
        print("ERROR: Found unpinned dependencies (using >=):")
        for dep in bad_deps:
            print(f"  - {dep}")
        return False

    # Check for == pinning
    pinned = re.findall(r'"([^"]+==[\d.]+.*?)"', deps_text)
    if pinned:
        print(f"✓ Found {len(pinned)} pinned production dependencies")
        return True

    print("ERROR: No pinned dependencies found")
    return False


def check_dev_dependencies() -> bool:
    """Verify pip-audit is in dev dependencies."""
    pyproject = Path("pyproject.toml").read_text()

    if "pip-audit" not in pyproject:
        print("ERROR: pip-audit not found in dev dependencies")
        return False

    if "pip-audit==" not in pyproject:
        print("ERROR: pip-audit is not pinned")
        return False

    version_match = re.search(r'pip-audit==([0-9.]+)', pyproject)
    if version_match:
        print(f"✓ pip-audit pinned to version {version_match.group(1)}")
        return True

    return False


def check_security_script() -> bool:
    """Verify security_check.py exists and has correct structure."""
    script_path = Path("scripts/security_check.py")

    if not script_path.exists():
        print("ERROR: scripts/security_check.py not found")
        return False

    content = script_path.read_text()

    required_elements = [
        "pip-audit",
        "--strict",
        "No known vulnerabilities",
    ]

    for element in required_elements:
        if element not in content:
            print(f"ERROR: Missing '{element}' in security_check.py")
            return False

    print("✓ security_check.py is properly configured")
    return True


def check_gitignore() -> bool:
    """Verify security patterns in .gitignore."""
    gitignore = Path(".gitignore").read_text()

    security_patterns = [
        ".pip-audit-cache",
        "*.pem",
        "*.key",
        "secrets.json",
        "credentials.json",
    ]

    missing = [p for p in security_patterns if p not in gitignore]

    if missing:
        print("ERROR: Missing security patterns in .gitignore:")
        for pattern in missing:
            print(f"  - {pattern}")
        return False

    print(f"✓ .gitignore includes {len(security_patterns)} security patterns")
    return True


def check_pre_commit_config() -> bool:
    """Verify .pre-commit-config.yaml exists and is valid."""
    config_path = Path(".pre-commit-config.yaml")

    if not config_path.exists():
        print("ERROR: .pre-commit-config.yaml not found")
        return False

    content = config_path.read_text()

    required_tools = [
        "ruff",
        "mypy",
        "pip-audit",
    ]

    for tool in required_tools:
        if tool not in content:
            print(f"ERROR: {tool} not found in .pre-commit-config.yaml")
            return False

    print("✓ .pre-commit-config.yaml includes all security tools")
    return True


def check_security_doc() -> bool:
    """Verify SECURITY.md documentation exists."""
    doc_path = Path("docs/SECURITY.md")

    if not doc_path.exists():
        print("ERROR: docs/SECURITY.md not found")
        return False

    content = doc_path.read_text()

    required_sections = [
        "Dependency Management",
        "Vulnerability Scanning",
        "Secrets Management",
        "Code Security Best Practices",
    ]

    for section in required_sections:
        if section not in content:
            print(f"ERROR: Missing '{section}' in SECURITY.md")
            return False

    print("✓ SECURITY.md documentation is complete")
    return True


def check_github_workflow() -> bool:
    """Verify GitHub Actions workflow exists."""
    workflow_path = Path(".github/workflows/security.yml")

    if not workflow_path.exists():
        print("ERROR: .github/workflows/security.yml not found")
        return False

    content = workflow_path.read_text()

    if "pip-audit" not in content:
        print("ERROR: pip-audit not configured in GitHub Actions")
        return False

    print("✓ GitHub Actions security workflow is configured")
    return True


def main() -> int:
    """Run all security verification checks."""
    print("=" * 70)
    print("PHX HOME ANALYSIS - SECURITY SETUP VERIFICATION")
    print("=" * 70)
    print()

    checks = [
        ("Pinned Dependencies", check_pinned_dependencies),
        ("Dev Dependencies (pip-audit)", check_dev_dependencies),
        ("Security Check Script", check_security_script),
        (".gitignore Patterns", check_gitignore),
        (".pre-commit-config.yaml", check_pre_commit_config),
        ("SECURITY.md Documentation", check_security_doc),
        ("GitHub Actions Workflow", check_github_workflow),
    ]

    results = []

    for name, check_func in checks:
        print(f"\n[*] Checking {name}...")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((name, False))

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")

    print("=" * 70)
    print(f"\nResult: {passed}/{total} checks passed")

    if passed == total:
        print("✓ All security checks passed!")
        return 0
    else:
        print(f"✗ {total - passed} check(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
