# Basalt

Basalt is the starting point for a small, cross-platform 3D game engine. The first milestone is deliberately limited to the engine core: a C++20 static library, generational entity handles, a scene, transforms, names, and generic component storage.

This is not yet a complete or production-ready game engine. There is no renderer, window/editor, physics, audio, scripting runtime, glTF importer, asset pipeline, or distributable game exporter in this initial foundation. Those systems need their own designs, implementations, tests, and platform validation before they can be called supported.

## Build and test

Requirements: CMake 3.24 or newer, a C++20 compiler, Git, and an internet connection for the first configure (CMake fetches pinned GLM and doctest releases).

```sh
cmake -S . -B build -DBASALT_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build build --config Debug --parallel
ctest --test-dir build --build-config Debug --output-on-failure
python -m unittest discover -s Tools/Delivery -p 'test_*.py' -v
```

The GitHub workflow builds the current source and runs tests on Windows, macOS, and Ubuntu. Uploaded change bundles are applied only in the workflow; the workflow commits the resulting source only after all three platform checks pass.

## Core API

`Basalt::Scene::CreateEntity` returns an entity handle with an index and generation. New entities receive a `Transform` component and may receive a `Name`. Components can be added, queried, iterated, and removed. Destroying an entity removes its components and invalidates its handle; when a slot is reused, the generation changes so the old handle stays stale.

Scene mutation is single-threaded. Component iteration order is unspecified. Adding or removing components while iterating the same component type is not supported. Component pointers are invalidated when that component is removed or its entity is destroyed.

## Project layout

- `include/Basalt/`: public engine headers
- `src/Basalt/`: engine implementation
- `tests/`: deterministic unit tests for implemented core behavior
- `Tools/Delivery/`: tested helper for applying text change bundles
- `AGENTS.md`: repository-wide development and review rules
- `.agents/skills/engine-development/`: task-specific development guide
