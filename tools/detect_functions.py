"""
Detect function boundaries for ICALL target addresses in the XBE binary.
Reads raw bytes from the .text section and uses simple heuristics:
- Look for CC padding or ret instructions before the target
- Look for ret/jmp/CC padding after to find the end
"""
import json
import struct
import sys

# Wreckless XBE layout
XBE_PATH = r"D:\recomp\xbox\wreckless\game\Wreckless - The Yakuza Missions\default.xbe"
FUNCTIONS_JSON = r"D:\recomp\xbox\wreckless\tools\disasm\output\functions.json"

# .text section: VA 0x11000, file offset needs to be computed from XBE header
# XBE base address
XBE_BASE = 0x10000

# ICALL targets to detect
TARGETS = [
    0x000E11A0, 0x000FB433,
]

def parse_xbe_sections(data):
    """Parse XBE header to get section VA->file offset mapping."""
    # XBE header
    cert_addr = struct.unpack_from('<I', data, 0x104)[0]
    num_sections = struct.unpack_from('<I', data, 0x11C)[0]
    section_headers_addr = struct.unpack_from('<I', data, 0x120)[0]

    # Section headers are at file offset = section_headers_addr - base_addr
    # But XBE uses virtual addresses in the header; the header itself is loaded at base_addr
    # The section header pointer is a VA, so offset = VA - base_addr
    sh_offset = section_headers_addr - XBE_BASE

    sections = []
    for i in range(num_sections):
        off = sh_offset + i * 0x38  # Each section header is 0x38 bytes
        # Section header: flags(4), va(4), va_size(4), raw_addr(4), raw_size(4), ...
        flags = struct.unpack_from('<I', data, off + 0x00)[0]
        va = struct.unpack_from('<I', data, off + 0x04)[0]
        va_size = struct.unpack_from('<I', data, off + 0x08)[0]
        raw_addr = struct.unpack_from('<I', data, off + 0x0C)[0]
        raw_size = struct.unpack_from('<I', data, off + 0x10)[0]

        sections.append({
            'va': va, 'va_size': va_size,
            'raw_addr': raw_addr, 'raw_size': raw_size,
        })
    return sections

def va_to_file_offset(va, sections):
    """Convert a virtual address to a file offset."""
    for s in sections:
        if s['va'] <= va < s['va'] + s['va_size']:
            return s['raw_addr'] + (va - s['va'])
    return None

def find_function_end(data, sections, start_va, max_search=512):
    """Find function end by looking for ret/jmp followed by CC padding or next function."""
    file_off = va_to_file_offset(start_va, sections)
    if file_off is None:
        return start_va + 16  # fallback

    i = 0
    last_ret = -1
    while i < max_search:
        if file_off + i >= len(data):
            break
        b = data[file_off + i]

        # C3 = ret, C2 xx xx = ret imm16
        if b == 0xC3:
            last_ret = i + 1
            # Check if followed by CC padding or another function prologue
            j = i + 1
            while j < max_search and file_off + j < len(data) and data[file_off + j] == 0xCC:
                j += 1
            if j > i + 1:  # CC padding after ret
                return start_va + last_ret
            # Check if next byte is a push ebp (55) - new function
            if file_off + j < len(data) and data[file_off + j] == 0x55:
                return start_va + last_ret
            # If just a simple ret with no padding, might still be the end
            # but could be mid-function. Keep scanning.
        elif b == 0xC2:  # ret imm16
            last_ret = i + 3
            i += 2  # skip the imm16
        elif b == 0xCC:  # int3 padding
            if last_ret > 0:
                return start_va + last_ret

        i += 1

    if last_ret > 0:
        return start_va + last_ret
    return start_va + 16  # fallback

def main():
    with open(XBE_PATH, 'rb') as f:
        data = f.read()

    sections = parse_xbe_sections(data)

    # Load existing functions
    with open(FUNCTIONS_JSON, 'r') as f:
        functions = json.load(f)

    existing_addrs = set()
    for func in functions:
        addr = int(func['start'], 16) if isinstance(func['start'], str) else func['start']
        existing_addrs.add(addr)

    # Build sorted list of all known boundaries
    all_boundaries = sorted(existing_addrs | set(TARGETS))

    new_functions = []
    for target in sorted(TARGETS):
        if target in existing_addrs:
            print(f"  0x{target:08X}: already in functions.json")
            continue

        # Find max size from next boundary
        idx = all_boundaries.index(target)
        if idx + 1 < len(all_boundaries):
            max_size = all_boundaries[idx + 1] - target
        else:
            max_size = 512

        # Find function end within the max size
        end_va = find_function_end(data, sections, target, max_search=max_size)
        size = min(end_va - target, max_size)

        # Quick sanity: read first few bytes
        file_off = va_to_file_offset(target, sections)
        if file_off and file_off + 4 <= len(data):
            first_bytes = ' '.join(f'{data[file_off+j]:02X}' for j in range(min(8, size)))
        else:
            first_bytes = '??'

        print(f"  0x{target:08X}: size={size:4d} bytes (max_gap={max_size}), first: {first_bytes}")
        new_functions.append({
            'address': f"0x{target:08X}",
            'size': size,
            'note': 'icall_target'
        })

    print(f"\nFound {len(new_functions)} new functions to add")

    # Output as JSON entries to paste
    print("\nJSON entries:")
    for nf in new_functions:
        print(f'  {{"address": "{nf["address"]}", "size": {nf["size"]}, "note": "{nf["note"]}"}},')

if __name__ == '__main__':
    main()
