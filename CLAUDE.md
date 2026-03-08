# Wreckless: The Yakuza Missions - Static Recompilation

## Project Overview
Static recompilation of the original Xbox game "Wreckless: The Yakuza Missions"
(internal codename: DSTEAL / Double Steal) into a native Windows PC executable.

## XBE Analysis
- **Title:** Wreckless: The Yakuza Missions
- **Title ID:** 0x4156000A
- **Base address:** 0x00010000
- **Entry point:** 0x000EB57E (→ xbe_entry_point)
- **Code size:** ~947 KB (.text section)
- **Total sections:** 11
- **Kernel imports:** 113 (all resolved: 56 bridged, 57 stub)

### Section Map (with raw file offsets)
| Section   | VA Start   | Size       | Raw Offset | Notes                    |
|-----------|-----------|------------|------------|--------------------------|
| .text     | 0x00011000 | 0x000E7760 | 0x00001000 | Game code (~947 KB)      |
| D3D       | 0x000F8760 | 0x00011908 | 0x000E9000 | Direct3D library         |
| D3DX      | 0x0010A080 | 0x0001CC50 | 0x000F8000 | D3DX extensions          |
| XGRPH     | 0x00126CE0 | 0x0000212C | 0x00115000 | Xbox graphics            |
| DSOUND    | 0x00128E20 | 0x00009674 | 0x00118000 | DirectSound              |
| WMVDEC    | 0x001324A0 | 0x00015350 | 0x0013D000 | WMV video decoder        |
| XPP       | 0x00147800 | 0x0000771C | 0x00122000 | Xbox Platform Plugin     |
| .rdata    | 0x0014EF20 | 0x000060D4 | 0x0012A000 | Read-only data           |
| .data     | 0x00155000 | 0x0007CE0C | 0x00131000 | Data + BSS (init: 20120) |
| DOLBY     | 0x001D1E20 | 0x00006D98 | 0x00136000 | Dolby audio              |
| $$XTIMAGE | 0x001D8BC0 | 0x00002800 | 0x00153000 | Title image              |

## Architecture
Based on the xboxrecomp framework and burnout3 reference project.

### Key Addresses
- **SEH prolog:** 0x000F0954 (__SEH_prolog)
- **SEH epilog:** 0x000F098D (__SEH_epilog)
- **Thread entry wrapper:** 0x000E8A42 (manually added to function list)
- **Game init:** 0x000EB50F (manually added, called via thread context)
- **Kernel thunk table:** 0x0014EF20 (113 entries)

### Build System
- CMake 3.20+ with MSVC (Visual Studio 2022), x64
- C11 standard, console subsystem (for debug output)
- Static libraries: xbox_kernel, d3d8_compat, dsound_compat, input_compat

### Pipeline
1. `tools.disasm` - Disassemble all sections (not --text-only)
2. `tools.func_id` - Identify/classify functions (9 CRT found)
3. `tools.recomp` - Lift x86 to C (276K lines, 3366/3398 translated)
4. CMake build - Compile native Windows executable (3.5MB)

### Key Directories
- `src/kernel/` - Xbox kernel -> Win32 compatibility layer (113 imports)
- `src/d3d/` - D3D8 -> D3D11 graphics translation
- `src/audio/` - DirectSound -> XAudio2
- `src/input/` - Xbox input -> XInput
- `src/game/` - Recompiled game code and entry point
- `src/game/recomp/gen/` - Auto-generated C source (git-ignored)
- `tools/` - xboxrecomp pipeline tools

## Progress
- [x] XBE parsed and analyzed
- [x] Project structure created
- [x] Kernel layer adapted (113 imports mapped, 56 bridged)
- [x] Memory layout configured with correct raw offsets
- [x] Full-section disassembly (3,407 functions)
- [x] Function identification (9 CRT + SEH prolog/epilog)
- [x] x86-to-C recompilation (276K lines)
- [x] First successful build (3.5MB MSVC x64)
- [x] First successful boot (10 kernel calls, heap allocation)
- [x] 6 new kernel functions pushed upstream to xboxrecomp
- [x] CRT heap initialization fixed (free list bin fixup)
- [x] Callee-saved register guard for indirect calls
- [x] CRT constructor table fully executed (20+ constructors)
- [x] Game main (sub_00021100) reached
- [ ] Fix stack corruption during CRT init (esp misaligned after sub_000EE98D)
- [ ] Debug game main crash (sub_00021100 → sub_00067B20)
- [ ] D3D8 translation for Wreckless rendering
- [ ] Audio/input integration

## Known Issues
- ~2000 unresolved sub_ symbols stubbed (disassembler missed function starts)
- 32 functions failed translation (complex instruction patterns)
- Stack corruption: CRT init (sub_000EE98D) leaks ~1527 bytes and misaligns esp by 1 byte
- Misidentified functions in DSOUND section (sub_0012FB19, sub_0012FB24, sub_0012FB2F) — stubbed
- HeapAlloc defensive fix: bins with Blink=0 are treated as empty (HeapCreate dead-code bug)
- 431 dead code switch targets cause callee-saved register corruption (guarded via ICALL macros)
- 57/113 kernel ordinals are stubs (return 0/success without real implementation)
