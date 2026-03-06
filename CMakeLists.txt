cmake_minimum_required(VERSION 3.20)
project(wreckless_recomp C)

# Wreckless: The Yakuza Missions - Static Recompilation
# Builds all compatibility layers and the recompiled game executable

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Common definitions
add_compile_definitions(
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)

# ── Compatibility layers (static libraries) ──────────────────

# Xbox kernel replacement (113 imports → Win32)
add_subdirectory(src/kernel)

# D3D8 → D3D11 graphics abstraction
add_subdirectory(src/d3d)

# DirectSound → XAudio2 audio abstraction
add_subdirectory(src/audio)

# Xbox input → XInput controller abstraction
add_subdirectory(src/input)

# ── Recompiled game executable ─────────────────────────────────
add_subdirectory(src/game)
