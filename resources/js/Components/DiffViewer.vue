<script setup>
/**
 * DiffViewer — sentence-aligned diff comparison with blob fallback.
 */
import { computed } from 'vue';

const props = defineProps({
    original: { type: String, default: '' },
    modified: { type: String, default: '' },
    segments: { type: Array, default: () => [] },
});

function normalizeWhitespace(value) {
    return String(value ?? '').replace(/\s+/g, ' ').trim();
}

/**
 * Simple word-level diff using longest common subsequence (LCS).
 * Returns array of { type: 'same' | 'removed' | 'added', text: string }
 */
function computeDiff(orig, mod) {
    const origWords = String(orig ?? '').split(/(\s+)/);
    const modWords = String(mod ?? '').split(/(\s+)/);

    const m = origWords.length;
    const n = modWords.length;
    const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (origWords[i - 1] === modWords[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    const result = [];
    let i = m;
    let j = n;

    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && origWords[i - 1] === modWords[j - 1]) {
            result.unshift({ type: 'same', text: origWords[i - 1] });
            i -= 1;
            j -= 1;
        } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
            result.unshift({ type: 'added', text: modWords[j - 1] });
            j -= 1;
        } else {
            result.unshift({ type: 'removed', text: origWords[i - 1] });
            i -= 1;
        }
    }

    const merged = [];
    for (const item of result) {
        if (merged.length > 0 && merged[merged.length - 1].type === item.type) {
            merged[merged.length - 1].text += item.text;
        } else {
            merged.push({ ...item });
        }
    }

    return merged;
}

function countWords(text) {
    return String(text ?? '').trim().split(/\s+/).filter(Boolean).length;
}

function computeStats(diffParts) {
    let added = 0;
    let removed = 0;
    let unchanged = 0;

    for (const part of diffParts) {
        const wordCount = countWords(part.text);
        if (part.type === 'added') added += wordCount;
        else if (part.type === 'removed') removed += wordCount;
        else unchanged += wordCount;
    }

    const base = unchanged + removed;
    const changePercent = base > 0 ? ((added + removed) / base) * 100 : 0;

    return {
        added,
        removed,
        unchanged,
        changePercent: Math.min(100, changePercent).toFixed(1),
    };
}

const alignedSegments = computed(() => {
    if (!Array.isArray(props.segments) || props.segments.length === 0) {
        return [];
    }

    return props.segments.map((segment, index) => {
        const originalText = String(segment?.original ?? segment?.text ?? '');
        const modifiedText = String(segment?.modified ?? originalText);
        const diff = computeDiff(originalText, modifiedText);

        return {
            id: segment?.id ?? `segment-${index}`,
            order: segment?.order ?? index,
            score: segment?.score ?? null,
            changed: segment?.changed ?? (normalizeWhitespace(originalText) !== normalizeWhitespace(modifiedText)),
            original: originalText,
            modified: modifiedText,
            diff,
        };
    });
});

const diffParts = computed(() => computeDiff(props.original, props.modified));

const stats = computed(() => {
    if (alignedSegments.value.length > 0) {
        const aggregate = alignedSegments.value.reduce((acc, segment) => {
            const segmentStats = computeStats(segment.diff);
            acc.added += segmentStats.added;
            acc.removed += segmentStats.removed;
            acc.unchanged += segmentStats.unchanged;
            acc.changedSegments += segment.changed ? 1 : 0;
            return acc;
        }, {
            added: 0,
            removed: 0,
            unchanged: 0,
            changedSegments: 0,
        });

        const base = aggregate.unchanged + aggregate.removed;
        const changePercent = base > 0 ? ((aggregate.added + aggregate.removed) / base) * 100 : 0;

        return {
            added: aggregate.added,
            removed: aggregate.removed,
            unchanged: aggregate.unchanged,
            changePercent: Math.min(100, changePercent).toFixed(1),
            changedSegments: aggregate.changedSegments,
            segmentCount: alignedSegments.value.length,
        };
    }

    return {
        ...computeStats(diffParts.value),
        changedSegments: null,
        segmentCount: null,
    };
});
</script>

<template>
    <div class="space-y-4">
        <div class="flex flex-wrap items-center gap-3 text-xs">
            <span class="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                +{{ stats.added }} ajoutés
            </span>
            <span class="flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 font-medium text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300">
                -{{ stats.removed }} supprimés
            </span>
            <span class="rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 font-medium text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">
                {{ stats.changePercent }}% modifié
            </span>
            <span
                v-if="stats.segmentCount !== null"
                class="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 font-medium text-indigo-700 dark:border-indigo-500/20 dark:bg-indigo-500/10 dark:text-indigo-300"
            >
                {{ stats.changedSegments }} / {{ stats.segmentCount }} phrases modifiées
            </span>
        </div>

        <div class="rounded-xl border border-zinc-200/60 bg-white p-5 dark:border-zinc-800/60 dark:bg-zinc-900/80">
            <div v-if="alignedSegments.length > 0" class="space-y-3">
                <div
                    v-for="(segment, index) in alignedSegments"
                    :key="segment.id"
                    class="rounded-lg border px-4 py-3 transition-colors"
                    :class="segment.changed
                        ? 'border-indigo-200/70 bg-indigo-50/40 dark:border-indigo-500/20 dark:bg-indigo-500/5'
                        : 'border-zinc-200/70 bg-zinc-50/60 dark:border-zinc-800 dark:bg-zinc-900/40'"
                >
                    <div class="mb-2 flex flex-wrap items-center gap-2 text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                        <span class="rounded-full border border-zinc-200 bg-white px-2 py-0.5 dark:border-zinc-700 dark:bg-zinc-800">
                            Phrase {{ index + 1 }}
                        </span>
                        <span
                            v-if="segment.score !== null"
                            class="rounded-full border border-zinc-200 bg-white px-2 py-0.5 dark:border-zinc-700 dark:bg-zinc-800"
                        >
                            {{ Number(segment.score).toFixed(1) }}% IA
                        </span>
                        <span
                            class="rounded-full px-2 py-0.5"
                            :class="segment.changed
                                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300'
                                : 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400'"
                        >
                            {{ segment.changed ? 'Remplacée' : 'Inchangée' }}
                        </span>
                    </div>

                    <p class="text-sm leading-8 text-zinc-700 dark:text-zinc-200">
                        <template v-for="(part, partIndex) in segment.diff" :key="`${segment.id}-${partIndex}`">
                            <span v-if="part.type === 'same'">{{ part.text }}</span>
                            <span v-else-if="part.type === 'removed'" class="rounded bg-rose-500/15 px-1 text-rose-700 line-through decoration-rose-500/50 dark:bg-rose-500/20 dark:text-rose-300">{{ part.text }}</span>
                            <span v-else class="rounded bg-emerald-500/15 px-1 font-medium text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300">{{ part.text }}</span>
                        </template>
                    </p>
                </div>
            </div>

            <p v-else class="text-sm leading-8 text-zinc-700 dark:text-zinc-200">
                <template v-for="(part, index) in diffParts" :key="index">
                    <span v-if="part.type === 'same'">{{ part.text }}</span>
                    <span v-else-if="part.type === 'removed'" class="rounded bg-rose-500/15 px-1 text-rose-700 line-through decoration-rose-500/50 dark:bg-rose-500/20 dark:text-rose-300">{{ part.text }}</span>
                    <span v-else class="rounded bg-emerald-500/15 px-1 font-medium text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300">{{ part.text }}</span>
                </template>
            </p>
        </div>
    </div>
</template>
