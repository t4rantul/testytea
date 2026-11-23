# Basalt development guidelines

These guidelines apply to every contribution in this repository.

## Project scope

- Basalt is a cross-platform C++ game-engine project. Keep the current implementation and future plans clearly distinguished in code, documentation, and release notes.
- Do not claim that rendering, physics, audio, scripting, editor, import, or game export features work until their code and automated tests exist.
- Keep platform-specific code behind narrow interfaces. Core scene and entity code must not depend on a window system, graphics API, or operating-system service.

## C++ style

- Follow the checked-in `.clang-format` file. Use four spaces, Allman braces, explicit includes, and no tabs.
- Put public headers under `include/Basalt/` and implementations under `src/Basalt/`; use the `Basalt` namespace.
- Use PascalCase for types, functions, and variables, consistent with Unreal Engine conventions. Use `b` prefixes for booleans only when that makes a condition clearer.
- Prefer value types, RAII, standard containers, and explicit ownership. Do not introduce owning raw pointers.
- Keep headers self-contained. Include the standard and third-party headers whose declarations are used; do not rely on transitive includes.
- Keep APIs small and document lifetime, thread-safety, and invalidation rules where relevant.
- Avoid global mutable state. Scene mutation is currently single-threaded; do not imply thread safety.

## Tests and changes

- Add deterministic unit tests for every new behavior, including invalid input, stale handles, removal, and cleanup paths.
- Keep tests independent of GPU, audio devices, network services, and wall-clock timing unless an integration test is explicitly isolated.
- A test scene must exercise every feature that exists in the current core. Add a corresponding test whenever a feature is added.
- Run `python -m unittest discover -s Tools/Delivery -p 'test_*.py' -v`, then configure, build, and run CTest using the commands in `README.md`.
- Before committing, review the complete diff for correctness, portability, API clarity, warnings, and tests. Do not commit generated build output or secrets.
- Changes delivered through `Incoming/` are reviewed and tested on Windows, macOS, and Ubuntu by the repository workflow before it creates a source commit.

## Dependencies and security

- Pin external dependencies to an explicit release or commit. Keep them out of checked-in source unless licensing or offline requirements justify vendoring.
- Never execute bundle contents as a shell script. The bundle helper treats uploaded input only as file data and rejects traversal, symlink escapes, protected workflow paths, and ambiguous edits.
- Do not add credentials, tokens, private keys, or machine-specific paths to the repository.
