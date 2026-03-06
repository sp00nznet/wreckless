# Wreckless: The Yakuza Missions - Static Recompilation

## Project Overview
Static recompilation of the original Xbox game "Wreckless: The Yakuza Missions"
(internal codename: DSTEAL / Double Steal) into a native Windows PC executable.

## XBE Analysis
- **Title:** Wreckless: The Yakuza Missions
- **Title ID:** 0x4156000A
- **Base address:** 0x00010000
- **Entry point:** 0x000EB57E
- **Code size:** ~947 KB (.text section)
- **Total sections:** 11
- **Kernel imports:** 113

### Section Map
| Section   | VA Start   | Size       | Notes                    |
|-----------|-----------|------------|--------------------------|
| .text     | 0x00011000 | 0x000E7760 | Game code (~947 KB)      |
| D3D       | 0x000F8760 | 0x00011908 | Direct3D library         |
| D3DX      | 0x0010A080 | 0x0001CC50 | D3DX extensions          |
| XGRPH     | 0x00126CE0 | 0x0000212C | Xbox graphics            |
| DSOUND    | 0x00128E20 | 0x00009674 | DirectSound              |
| WMVDEC    | 0x001324A0 | 0x00015350 | WMV video decoder        |
| XPP       | 0x00147800 | 0x0000771C | Xbox Platform Plugin     |
| .rdata    | 0x0014EF20 | 0x000060D4 | Read-only data           |
| .data     | 0x00155000 | 0x0007CE0C | Data + BSS               |
| DOLBY     | 0x001D1E20 | 0x00006D98 | Dolby audio              |
| $$XTIMAGE | 0x001D8BC0 | 0x00002800 | Title image              |

## Architecture
Based on the xboxrecomp framework and burnout3 reference project.

### Build System
- CMake 3.20+ with MSVC (Visual Studio 2022)
- C11 standard
- Static libraries: xbox_kernel, d3d8_compat, dsound_compat, input_compat

### Pipeline
1. `tools.xbe_parser` - Parse XBE headers and sections
2. `tools.disasm` - Disassemble .text section
3. `tools.func_id` - Identify/classify functions
4. `tools.recomp` - Lift x86 to C source code
5. CMake build - Compile native Windows executable

### Key Directories
- `src/kernel/` - Xbox kernel → Win32 compatibility layer (113 imports)
- `src/d3d/` - D3D8 → D3D11 graphics translation
- `src/audio/` - DirectSound → XAudio2
- `src/input/` - Xbox input → XInput
- `src/game/` - Recompiled game code and entry point
- `tools/` - Symlink/copy of xboxrecomp pipeline tools
- `docs/` - Technical documentation

## Progress
- [x] XBE parsed and analyzed
- [x] Project structure created
- [x] Kernel layer adapted (113 imports mapped)
- [x] Memory layout configured for Wreckless sections
- [ ] Disassembly pipeline run
- [ ] Function identification
- [ ] x86-to-C recompilation
- [ ] First successful build
- [ ] First successful boot
