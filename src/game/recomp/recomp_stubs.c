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

/* No manual overrides yet - return NULL for all VAs */
recomp_func_t recomp_lookup_manual(uint32_t xbox_va)
{
    (void)xbox_va;
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
