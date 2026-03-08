/**
 * Recompilation runtime stubs
 *
 * Provides the runtime support functions needed by generated code:
 * - recomp_lookup_manual: manual function overrides (none yet)
 * - recomp_icall_fail_log: indirect call failure diagnostics
 * - ICALL trace ring buffer globals
 */

#include <stdio.h>
#include <stdint.h>

/* ICALL trace ring buffer - defined in xbox_memory_layout.c */
extern volatile uint32_t g_icall_trace[16];
extern volatile uint32_t g_icall_trace_idx;
extern volatile uint64_t g_icall_count;

typedef void (*recomp_func_t)(void);

/* Forward declarations for functions we want to trace */
extern void sub_000EE1B0(void);  /* CRT heap init */
extern void sub_000EC7D3(void);  /* CRT HeapCreate */
extern uint32_t g_eax;
extern ptrdiff_t g_xbox_mem_offset;

/**
 * Fix up CRT heap free list bins after HeapCreate.
 *
 * The MSVC CRT heap descriptor has 128 small-block bins at offset 0x180,
 * each an 8-byte LIST_ENTRY {Flink, Blink}. Empty bins must be circular
 * (both pointers point to the bin's own Xbox VA). HeapCreate should
 * initialize these, but the recompiled code has dead-code bugs that cause
 * incomplete initialization, leaving some bins zeroed. A zeroed bin
 * looks non-empty (Flink != self), so HeapAlloc tries to unlink from it
 * and crashes on the null pointer.
 *
 * Fix: after HeapCreate, scan all 128 bins and initialize any that
 * are still zeroed to self-pointing empty lists.
 */
void fixup_heap_freelists(uint32_t heap_handle)
{
    fprintf(stderr, "  [HEAP-FIX] fixup_heap_freelists(0x%08X) called\n", heap_handle);
    fflush(stderr);
    if (!heap_handle) return;

    int fixed = 0;
    int already_ok = 0;
    int had_entries = 0;
    for (int i = 0; i < 128; i++) {
        uint32_t bin_va = heap_handle + 0x180 + i * 8;
        volatile uint32_t *flink = (volatile uint32_t *)((uintptr_t)bin_va + g_xbox_mem_offset);
        volatile uint32_t *blink = flink + 1;

        /* A valid empty bin has both Flink and Blink pointing to itself.
         * A valid non-empty bin has both pointing to valid heap addresses.
         * A broken bin has either field as 0, or Flink != self with Blink == 0. */
        if (*flink == bin_va && *blink == bin_va) {
            already_ok++;  /* properly empty */
        } else if (*flink == 0 || *blink == 0) {
            /* Corrupt: at least one pointer is NULL */
            if (i < 8 || *flink != 0 || *blink != 0) {
                fprintf(stderr, "  [HEAP-FIX] bin[%d] @ 0x%08X: Flink=0x%08X Blink=0x%08X → fixing\n",
                        i, bin_va, *flink, *blink);
            }
            *flink = bin_va;
            *blink = bin_va;
            fixed++;
        } else {
            had_entries++;  /* has real entries, don't touch */
        }
    }
    fprintf(stderr, "  [HEAP-FIX] Result: fixed=%d empty_ok=%d has_entries=%d at heap 0x%08X\n",
            fixed, already_ok, had_entries, heap_handle);
    fflush(stderr);
}

static void traced_sub_000EE1B0(void)
{
    fprintf(stderr, "  [TRACE] sub_000EE1B0 (CRT heap init) ENTERED\n");
    fflush(stderr);
    sub_000EE1B0();
    uint32_t heap_handle = *(volatile uint32_t *)((uintptr_t)0x1D1A10 + g_xbox_mem_offset);
    fprintf(stderr, "  [TRACE] sub_000EE1B0 RETURNED, heap_handle=0x%08X, eax=0x%08X\n",
            heap_handle, g_eax);
    fflush(stderr);
    fixup_heap_freelists(heap_handle);
}

static void traced_sub_000EC7D3(void)
{
    fprintf(stderr, "  [TRACE] sub_000EC7D3 (HeapCreate) ENTERED\n");
    fflush(stderr);
    sub_000EC7D3();
    fprintf(stderr, "  [TRACE] sub_000EC7D3 RETURNED, eax=0x%08X\n", g_eax);
    fflush(stderr);
}

/* Manual overrides for tracing CRT heap init */
recomp_func_t recomp_lookup_manual(uint32_t xbox_va)
{
    if (xbox_va == 0x000EE1B0) return traced_sub_000EE1B0;
    if (xbox_va == 0x000EC7D3) return traced_sub_000EC7D3;
    return (recomp_func_t)0;
}

/* Log failed indirect call resolution */
void recomp_icall_fail_log(uint32_t va)
{
    fprintf(stderr, "[ICALL] Failed to resolve VA 0x%08X (total calls: %llu)\n",
            va, (unsigned long long)g_icall_count);

    /* Dump last 16 call targets */
    fprintf(stderr, "  Recent ICALL targets:\n");
    for (int i = 0; i < 16; i++) {
        int idx = (g_icall_trace_idx - 16 + i) & 15;
        if (g_icall_trace[idx])
            fprintf(stderr, "    [%2d] 0x%08X\n", i, g_icall_trace[idx]);
    }
}
