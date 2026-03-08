"""
Post-processing patches for generated recomp code.
Fixes known lifter bugs that need to be applied after each pipeline run.
"""
import re
import sys

GEN_DIR = r"D:\recomp\xbox\wreckless\src\game\recomp\gen"

patches_applied = 0

def patch_file(filepath, patches):
    """Apply a list of (old, new, description) patches to a file."""
    global patches_applied
    with open(filepath, 'r') as f:
        content = f.read()

    for old, new, desc in patches:
        if old in content:
            content = content.replace(old, new, 1)
            patches_applied += 1
            print(f"  [OK] {desc}")
        else:
            print(f"  [SKIP] {desc} - pattern not found")

    with open(filepath, 'w') as f:
        f.write(content)


def patch_recomp_0002():
    """Fix memcpy dead code labels and HeapCreate success path."""
    filepath = f"{GEN_DIR}/recomp_0002.c"
    patches = []

    # Fix 1: memcpy epilog - add loc_000F0418 label before loc_000F0420
    patches.append((
        "loc_000F0420:\n"
        "    SET_LO8(eax, MEM8(esi));\n"
        "    MEM8(edi) = LO8(eax);\n"
        "    eax = MEM32(ebp + 8);\n"
        "    POP32(esp, esi);\n"
        "    POP32(esp, edi);\n"
        "    esp = ebp;\n"
        "    POP32(esp, ebp); /* leave */\n"
        "    esp += 4; return; /* ret */",

        "loc_000F0418: /* epilog: no remainder bytes */\n"
        "    eax = MEM32(ebp + 8);\n"
        "    POP32(esp, esi);\n"
        "    POP32(esp, edi);\n"
        "    esp = ebp;\n"
        "    POP32(esp, ebp); /* leave */\n"
        "    esp += 4; return; /* ret */\n"
        "\n"
        "loc_000F0420:\n"
        "    SET_LO8(eax, MEM8(esi));\n"
        "    MEM8(edi) = LO8(eax);\n"
        "    eax = MEM32(ebp + 8);\n"
        "    POP32(esp, esi);\n"
        "    POP32(esp, edi);\n"
        "    esp = ebp;\n"
        "    POP32(esp, ebp); /* leave */\n"
        "    esp += 4; return; /* ret */",

        "memcpy: add loc_000F0418 epilog label"
    ))

    # Fix 2: memcpy switch table - fix all dead code targets for 0xF0418
    # This needs replace_all behavior
    patches.append(None)  # placeholder, handled separately

    # Fix 3: memcpy switch table - fix dead code target for 0xF03BC
    patches.append(None)  # placeholder

    # Fix 4: HeapCreate success path - add g_seh_ebp = ebp before sub_000ECB82
    patches.append((
        "sub_000ECB82(); return; } /* jne: not equal / not zero */",
        "g_seh_ebp = ebp; sub_000ECB82(); return; } /* jne: not equal / not zero */",
        "HeapCreate: add g_seh_ebp before sub_000ECB82 tail call"
    ))

    # Fix 5: HeapAlloc crash - fix heap free list bins after sub_000EE1B0 returns.
    # HeapCreate has dead-code bugs that leave some bins with Flink set but Blink=0.
    # This causes HeapAlloc to read Blink=0, subtract 8 → 0xFFFFFFF8, then crash.
    patches.append((
        "    PUSH32(esp, 0); sub_000EE1B0(); /* call 0x000EE1B0 */\n"
        "\n"
        "loc_000EB514:",

        "    PUSH32(esp, 0); sub_000EE1B0(); /* call 0x000EE1B0 */\n"
        "    { extern void fixup_heap_freelists(uint32_t); fixup_heap_freelists(MEM32(0x1D1A10)); }\n"
        "\n"
        "loc_000EB514:",

        "sub_000EB50F: fixup heap free list bins after CRT heap init"
    ))

    # Fix 6: sub_000ECB82 - add fall-through to SEH epilog (sub_000ECBEF)
    patches.append((
        "    eax = MEM32(ebp + -28);\n"
        "\n"
        "}\n"
        "\n"
        "/**\n"
        " * sub_000ECBEF",

        "    eax = MEM32(ebp + -28);\n"
        "    g_seh_ebp = ebp; sub_000ECBEF(); return; /* fall-through to SEH epilog */\n"
        "\n"
        "}\n"
        "\n"
        "/**\n"
        " * sub_000ECBEF",

        "sub_000ECB82: add fall-through to sub_000ECBEF"
    ))

    # Apply simple patches
    with open(filepath, 'r') as f:
        content = f.read()

    for patch in patches:
        if patch is None:
            continue
        old, new, desc = patch
        if old in content:
            content = content.replace(old, new, 1)
            global patches_applied
            patches_applied += 1
            print(f"  [OK] {desc}")
        else:
            print(f"  [SKIP] {desc} - pattern not found")

    # Replace all: fix 0xF0418 dead code targets
    old_switch = 'if (_jt == 0x000F0418u) (void)0; /* goto loc_000F0418 - dead code, label not in function */'
    new_switch = 'if (_jt == 0x000F0418u) goto loc_000F0418; /* epilog: restore regs and return */'
    count = content.count(old_switch)
    if count > 0:
        content = content.replace(old_switch, new_switch)
        patches_applied += count
        print(f"  [OK] memcpy: fix {count} switch entries for 0xF0418")
    else:
        print(f"  [SKIP] memcpy: 0xF0418 switch entries not found")

    # Fix 0xF03BC dead code target
    old_3bc = 'if (_jt == 0x000F03BCu) (void)0; /* goto loc_000F03BC - dead code, label not in function */'
    new_3bc = 'if (_jt == 0x000F03BCu) goto loc_000F03FF; /* ecx=0: no dwords, skip to remainder */'
    count = content.count(old_3bc)
    if count > 0:
        content = content.replace(old_3bc, new_3bc)
        patches_applied += count
        print(f"  [OK] memcpy: fix {count} switch entries for 0xF03BC")

    with open(filepath, 'w') as f:
        f.write(content)


def main():
    global patches_applied
    print("Applying post-generation patches...")
    print(f"\nPatching recomp_0002.c:")
    patch_recomp_0002()
    print(f"\nDone: {patches_applied} patches applied")


if __name__ == '__main__':
    main()
