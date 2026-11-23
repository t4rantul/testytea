# Roadmap

This roadmap records intended work, not implemented capability. Each phase needs design review, unit or integration tests, and supported-platform CI before it is considered complete.

1. **Core foundation (current):** CMake project, entity lifecycle, scene, transforms, names, generic component storage, and unit tests.
2. **Runtime foundation:** logging, configuration, resource lifetime rules, frame loop, application/window abstraction, and platform smoke tests.
3. **Rendering:** Vulkan device/swapchain setup through GLFW, NVRHI abstraction, glTF asset ingestion, PBR materials, HDR/tonemapping, IBL, shadows, and SSAO. Validate on real hardware and software-rendered CI where available.
4. **Physics and audio:** select and pin libraries, define ownership and fixed-step behavior, integrate Steam Audio where its platform/license requirements fit, and test deterministically.
5. **Scripting:** embed Luau behind a capability-limited API; test entity/component access, update callbacks, spawn/destroy, error handling, and script lifetime.
6. **Authoring and distribution:** editor scene tooling and gizmos, project/asset packaging, headless runtime build, and exported-game smoke tests.

Do not treat a roadmap item as a promise of delivery until code, documentation, and tests land.
