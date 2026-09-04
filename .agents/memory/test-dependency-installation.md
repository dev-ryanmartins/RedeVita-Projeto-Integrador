---
name: Test dependency installation
description: Packaging behavior to verify when adding Python-only test tooling.
---

When adding a Python test tool through the workspace package installer, verify
the resulting `pyproject.toml` keeps it in a test/development group rather
than the default runtime dependency list, then regenerate and check the lockfile.

**Why:** The workspace installer uses `uv add`, which can place a requested
test package in the main dependency list even when the project intends it to be
optional.

**How to apply:** After installing test tooling, inspect both dependency
sections, run the lockfile consistency check, and validate the test extra from
the project root.