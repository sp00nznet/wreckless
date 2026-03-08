"""Add ICALL target functions to functions.json."""
import json

FUNCTIONS_JSON = r"D:\recomp\xbox\wreckless\tools\disasm\output\functions.json"

NEW_ENTRIES = [
    ("0x000F8010", 48), ("0x000F8040", 24), ("0x000F8060", 24), ("0x000F8080", 24),
    ("0x000F80A0", 24), ("0x000F80C0", 24), ("0x000F80E0", 24), ("0x000F8100", 24),
    ("0x000F8120", 24), ("0x000F8140", 22), ("0x000F8160", 22), ("0x000F8180", 22),
    ("0x000F81A0", 22), ("0x000F81C0", 22), ("0x000F81E0", 22), ("0x000F8200", 22),
    ("0x000F8220", 22), ("0x000F8240", 22), ("0x000F8260", 22), ("0x000F8280", 22),
    ("0x000F82A0", 12), ("0x000F82B0", 22), ("0x000F82D0", 45), ("0x000F8300", 12),
    ("0x000F8310", 22), ("0x000F8330", 12), ("0x000F8340", 12), ("0x000F8350", 12),
    ("0x000F8360", 14), ("0x000F8370", 11), ("0x000F8380", 14), ("0x000F8390", 12),
    ("0x000F83A0", 12), ("0x000F83B0", 12), ("0x000F83C0", 22), ("0x000F83E0", 38),
    ("0x000F8410", 45), ("0x000F8440", 41), ("0x000F8470", 13), ("0x000F8480", 12),
    ("0x000F8490", 673), ("0x000FB370", 45), ("0x0012FB19", 11), ("0x0012FB24", 11),
    ("0x00148AC7", 56),
    # Dependencies of the above
    ("0x000E11A0", 89), ("0x000FB433", 3),
]

with open(FUNCTIONS_JSON, 'r') as f:
    functions = json.load(f)

existing = {int(fn['start'], 16) for fn in functions}

added = 0
for addr_str, size in NEW_ENTRIES:
    addr = int(addr_str, 16)
    if addr in existing:
        continue
    end = addr + size
    entry = {
        'start': f"0x{addr:08X}",
        'end': f"0x{end:08X}",
        'size': size,
        'name': f"sub_{addr:08X}",
        'section': '.text',
        'confidence': 0.9,
        'detection_method': 'icall_target',
        'num_instructions': size // 3,  # rough estimate
        'has_prologue': False,
        'calls_to': [],
        'called_by': [],
    }
    functions.append(entry)
    added += 1

# Sort by start address
functions.sort(key=lambda f: int(f['start'], 16))

with open(FUNCTIONS_JSON, 'w') as f:
    json.dump(functions, f, indent=2)

print(f"Added {added} new functions. Total: {len(functions)}")
