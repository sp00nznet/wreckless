# Wreckless: The Yakuza Missions - Static Recompilation

A static recompilation of the original Xbox game **Wreckless: The Yakuza Missions**
(internal codename: DSTEAL / Double Steal) into a native Windows PC executable.

This project translates the game's original x86 machine code into portable C source
code, which is then compiled to a native x86-64 Windows binary. No emulation is
involved at runtime.

## Status

| Phase | Status | Details |
|-------|--------|---------|
| XBE Parsing | Done | 11 sections, 113 kernel imports identified |
| Disassembly | Done | All sections, 3,407 functions (incl. 2 manual) |
| Function ID | Done | 9 CRT, 1 SEH prolog, 1 SEH epilog identified |
| Recompilation | Done | 276,452 lines of C across 4 source files |
| Kernel Layer | Done | 113/113 resolved (56 bridged, 57 stub), 6 new functions |
| First Build | Done | 3.5MB wreckless.exe (MSVC x64 Release) |
| First Boot | Done | Game executes ~10 kernel calls, allocates heap, then crashes |
| Graphics (D3D8->D3D11) | Scaffolded | Compatibility layer from burnout3 baseline |
| Audio (DS->XAudio2) | Scaffolded | Compatibility layer from burnout3 baseline |
| Input (XPP->XInput) | Scaffolded | Compatibility layer from burnout3 baseline |
| Gameplay | Not Started | Debugging early init crash (null pointer in data setup) |

## XBE Analysis

| Property | Value |
|----------|-------|
| Title | Wreckless: The Yakuza Missions |
| Title ID | 0x4156000A |
| Base Address | 0x00010000 |
| Entry Point | 0x000EB57E |
| Code Size | ~947 KB (.text) |
| Total Sections | 11 |
| Kernel Imports | 113 |
| Functions | 3,407 (all sections, incl. 2 manual) |
| Translated | 3,366 (32 failed) |
| Kernel Thunks | 113/113 resolved (56 bridged, 57 stub) |

### Memory Map

```
0x00011000 - 0x000F8760  .text     (947 KB)   Game code
0x000F8760 - 0x0010A068  D3D       (73 KB)    Direct3D library
0x0010A080 - 0x00126CD0  D3DX      (115 KB)   D3DX extensions
0x00126CE0 - 0x00128E0C  XGRPH     (8 KB)     Xbox graphics
0x00128E20 - 0x00132494  DSOUND    (38 KB)    DirectSound
0x001324A0 - 0x001477F0  WMVDEC    (85 KB)    WMV video decoder
0x00147800 - 0x0014EF1C  XPP       (30 KB)    Xbox Platform Plugin
0x0014EF20 - 0x00154FF4  .rdata    (24 KB)    Constants
0x00155000 - 0x001D1E0C  .data     (500 KB)   Data + BSS
0x001D1E20 - 0x001D8BB8  DOLBY     (27 KB)    Dolby audio
0x001D8BC0 - 0x001DB3C0  $$XTIMAGE (10 KB)    Title image
```

## Building

### Prerequisites

- Windows 11
- Visual Studio 2022 (MSVC compiler)
- CMake 3.20+
- Python 3.10+ with `capstone` (`pip install capstone`)

### Pipeline (generate recompiled code)

```bash
# 1. Parse XBE
py -3 -c "from tools.xbe_parser.xbe_parser import XBEParser; ..."

# 2. Disassemble
py -3 -m tools.disasm "game/Wreckless - The Yakuza Missions/default.xbe" \
    --analysis-json "game/Wreckless - The Yakuza Missions/default_analysis.json" -v

# 3. Identify functions
py -3 -m tools.func_id "game/Wreckless - The Yakuza Missions/default.xbe" \
    --functions tools/disasm/output/functions.json \
    --strings tools/disasm/output/strings.json \
    --xrefs tools/disasm/output/xrefs.json -v

# 4. Recompile to C
py -3 -m tools.recomp "game/Wreckless - The Yakuza Missions/default.xbe" \
    --all --split 1000 --gen-dir src/game/recomp/gen -v
```

### Build (compile native executable)

```bash
cmake -B build -G "Visual Studio 17 2022"
cmake --build build --config Release
```

## Architecture

Built on the [xboxrecomp](https://github.com/sp00nznet/xboxrecomp) framework,
following the same architecture as the
[burnout3](https://github.com/sp00nznet/burnout3) reference implementation.

```
wreckless/
  src/
    kernel/     Xbox kernel -> Win32 (113 imports)
    d3d/        D3D8 -> D3D11 graphics translation
    audio/      DirectSound -> XAudio2
    input/      Xbox input -> XInput
    game/       Recompiled game code + entry point
      recomp/
        gen/    Auto-generated C source (276K lines, git-ignored)
  tools/        xboxrecomp pipeline (disasm, func_id, recomp)
  docs/         Technical documentation
  game/         Original game files (git-ignored)
```

## Boot Log

Current boot progress (game executes through initialization before crashing):
```
PsCreateSystemThreadEx #1: routine=0x000E8A42 (thread entry wrapper)
  → SEH prolog setup
  → Game init (sub_000EB50F) called via thread context
  → RtlInitializeCriticalSection, KeInitializeEvent
  → NtAllocateVirtualMemory: 1MB heap allocated
  → Crash: null pointer dereference during data structure init
```

### Kernel calls executed before crash
| # | Ordinal | Function | Result |
|---|---------|----------|--------|
| 1 | 255 | PsCreateSystemThreadEx | OK - main thread created |
| 2 | 277 | RtlInitializeCriticalSection | OK |
| 3 | 107 | KeInitializeEvent | OK |
| 4 | 113 | KeInitializeEvent | OK |
| 5 | 24 | ExInitializeReadWriteLock | OK (stub) |
| 6 | 301 | NtQuerySystemTime | OK |
| 7-8 | 184 | NtAllocateVirtualMemory | OK - 1MB allocated |
| 9 | 291 | RtlLeaveCriticalSection | OK |
| 10 | 277 | RtlInitializeCriticalSection | OK |

## Technical Notes

- Wreckless uses a **custom engine** (not RenderWare), making function identification
  more challenging than RenderWare-based games
- The game has extensive use of XDK libraries (D3D, D3DX, DSOUND, WMVDEC) in separate
  PE sections, which helps isolate game-specific code
- SEH prolog/epilog at 0x000F0954/0x000F098D (MSVC __SEH_prolog pattern)
- Thread entry wrapper at 0x000E8A42 copies init data and calls game main via context pointer
- Internal codename "DSTEAL" / "Double Steal" (the Japanese title)
- Multiple regional XBE variants exist (US, UK, FR, GR, JP)
- The JP/FR/GR variants are larger (~1.9 MB vs ~1.4 MB) suggesting additional content

### New kernel functions (contributed to xboxrecomp)
| Ordinal | Function | Description |
|---------|----------|-------------|
| 7 | DbgPrint | Debug printf (__cdecl, variadic) |
| 5 | KdDebuggerNotPresent | Data export: debugger absent flag |
| 125 | KeQueryInterruptTime | Monotonic time in 100ns units |
| 302 | NtResumeThread | Resume suspended thread |
| 304 | NtSuspendThread | Suspend thread |

## License

This project contains no copyrighted game assets. You must provide your own copy
of the original game. The recompilation tools and compatibility layers are provided
for educational and preservation purposes.
