---
name: Basalt Engine Development
description: Use when changing Basalt engine code, tests, architecture, build configuration, or contributor documentation.
---

# Basalt engine development

- Read `AGENTS.md` and the relevant public headers before changing engine behavior.
- Confirm the code exists before describing a capability as implemented. Keep renderer, editor, physics, audio, scripting, asset import, and export work explicitly marked as planned until implemented and tested.
- Preserve the public API's ownership, lifetime, thread-safety, and invalidation guarantees. Scene mutation is single-threaded in this foundation.
- Use the repository's `.clang-format`; follow Unreal-style PascalCase naming and Allman braces.
- Add focused doctest unit tests for success, failure, stale-handle, and cleanup behavior. Avoid GPU/device requirements in core unit tests.
- Run the Python delivery-helper tests, CMake build, and CTest suite. The GitHub workflow repeats the engine build and tests on Windows, macOS, and Ubuntu before a bundle is committed.
- Review the full diff and dependency changes before committing. Do not modify workflow files through a change bundle.
