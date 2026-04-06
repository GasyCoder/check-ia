<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
    result: { type: Number, required: true },
    chunkResults: { type: Array, default: null },
    sentences: { type: Array, default: null },
    preprocessing: { type: Object, default: null },
});

const expandedChunks = ref({});

function toggleChunk(i) {
    expandedChunks.value[i] = !expandedChunks.value[i];
}

const aiScore = computed(() => normalizePercent(props.result));
const humanScore = computed(() => Math.max(0, 100 - aiScore.value));
const humanPercent = computed(() => humanScore.value.toFixed(1));
const aiPercent = computed(() => aiScore.value.toFixed(1));
const copied = ref(false);

function normalizePercent(value) {
    const numeric = Number(value);

    if (!Number.isFinite(numeric)) return 0;

    if (numeric >= 0 && numeric <= 1) {
        return Math.min(100, Math.max(0, numeric * 100));
    }

    return Math.min(100, Math.max(0, numeric));
}

function scoreMeta(score) {
    const value = normalizePercent(score);

    if (value >= 80) {
        return {
            title: 'IA détectée',
            subtitle: 'Ce texte présente un signal fort de génération par intelligence artificielle.',
            shortLabel: 'IA',
            dot: 'bg-red-500',
            bar: 'bg-red-500',
            textColor: 'text-red-600 dark:text-red-400',
            sentence: 'border-red-500/25 bg-red-500/20 text-red-800 dark:border-red-400/25 dark:bg-red-500/20 dark:text-red-200',
            badge: 'bg-red-500/10 text-red-700 dark:bg-red-500/15 dark:text-red-300 border-red-500/20 dark:border-red-400/20',
            legendText: 'text-red-600 dark:text-red-400',
            legendSwatch: 'border-red-500/25 bg-red-500/20 dark:border-red-400/25 dark:bg-red-500/20',
        };
    }

    if (value >= 60) {
        return {
            title: 'Probablement IA',
            subtitle: 'Ce texte contient plusieurs signaux typiques d’un contenu généré par IA.',
            shortLabel: 'Prob. IA',
            dot: 'bg-orange-500',
            bar: 'bg-orange-500',
            textColor: 'text-orange-600 dark:text-orange-400',
            sentence: 'border-orange-500/25 bg-orange-500/20 text-orange-800 dark:border-orange-400/25 dark:bg-orange-500/20 dark:text-orange-200',
            badge: 'bg-orange-500/10 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300 border-orange-500/20 dark:border-orange-400/20',
            legendText: 'text-orange-600 dark:text-orange-400',
            legendSwatch: 'border-orange-500/25 bg-orange-500/20 dark:border-orange-400/25 dark:bg-orange-500/20',
        };
    }

    if (value >= 30) {
        return {
            title: 'Incertain',
            subtitle: 'Le texte présente un mélange de signaux humains et artificiels.',
            shortLabel: 'Incertain',
            dot: 'bg-amber-500',
            bar: 'bg-amber-500',
            textColor: 'text-amber-600 dark:text-amber-400',
            sentence: 'border-amber-500/25 bg-amber-500/20 text-amber-800 dark:border-amber-400/25 dark:bg-amber-500/20 dark:text-amber-200',
            badge: 'bg-amber-500/10 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300 border-amber-500/20 dark:border-amber-400/20',
            legendText: 'text-amber-600 dark:text-amber-400',
            legendSwatch: 'border-amber-500/25 bg-amber-500/20 dark:border-amber-400/25 dark:bg-amber-500/20',
        };
    }

    return {
        title: 'Écrit par un humain',
        subtitle: 'Ce texte est très probablement rédigé par un être humain.',
        shortLabel: 'Humain',
        dot: 'bg-emerald-500',
        bar: 'bg-emerald-500',
        textColor: 'text-emerald-600 dark:text-emerald-400',
        sentence: 'border-emerald-500/25 bg-emerald-500/20 text-emerald-800 dark:border-emerald-400/25 dark:bg-emerald-500/20 dark:text-emerald-200',
        badge: 'bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300 border-emerald-500/20 dark:border-emerald-400/20',
        legendText: 'text-emerald-600 dark:text-emerald-400',
        legendSwatch: 'border-emerald-500/25 bg-emerald-500/20 dark:border-emerald-400/25 dark:bg-emerald-500/20',
    };
}

function sentenceMeta(score) {
    const value = normalizePercent(score);

    if (value >= 76) {
        return {
            textColor: 'text-red-800 dark:text-red-200',
            badge: 'border-red-500/30 bg-red-500/15 shadow-[inset_4px_0_0_rgba(239,68,68,0.85)] dark:border-red-400/30 dark:bg-red-500/20',
        };
    }

    if (value >= 51) {
        return {
            textColor: 'text-orange-800 dark:text-orange-200',
            badge: 'border-orange-500/30 bg-orange-500/15 shadow-[inset_4px_0_0_rgba(249,115,22,0.8)] dark:border-orange-400/30 dark:bg-orange-500/20',
        };
    }

    if (value >= 26) {
        return {
            textColor: 'text-amber-900 dark:text-amber-100',
            badge: 'border-amber-400/35 bg-amber-300/20 shadow-[inset_4px_0_0_rgba(234,179,8,0.75)] dark:border-amber-300/30 dark:bg-amber-400/15',
        };
    }

    return {
        textColor: 'text-emerald-800 dark:text-emerald-200',
        badge: 'border-emerald-500/30 bg-emerald-500/10 shadow-[inset_4px_0_0_rgba(34,197,94,0.78)] dark:border-emerald-400/30 dark:bg-emerald-500/15',
    };
}

const v = computed(() => {
    return scoreMeta(props.result);
});

const needleAngle = computed(() => -90 + (props.result / 100) * 180);

function barColor(val) {
    return scoreMeta(val).bar;
}

function authenticityBarColor(val) {
    const humanValue = normalizePercent(val);

    if (humanValue > 60) {
        return 'bg-emerald-500';
    }

    if (humanValue >= 40) {
        return 'bg-amber-500';
    }

    return 'bg-red-500';
}

function sentenceVisualScore(score, contextScore = props.result) {
    const sentenceScore = normalizePercent(score);
    const context = normalizePercent(contextScore);

    if (context >= 26 && context <= 50) {
        if (sentenceScore >= 18) {
            return Math.max(sentenceScore, 28);
        }

        return sentenceScore;
    }

    if (context >= 51 && context <= 75) {
        if (sentenceScore >= 34) {
            return Math.max(sentenceScore, 52);
        }

        return sentenceScore;
    }

    if (context >= 76 && sentenceScore >= 50) {
        return Math.max(sentenceScore, 76);
    }

    return sentenceScore;
}

function sentenceClasses(score, contextScore = props.result) {
    const meta = sentenceMeta(sentenceVisualScore(score, contextScore));

    return [
        'inline-block rounded-md border px-2 py-1 transition-all duration-300 ease-out cursor-default',
        'hover:-translate-y-[1px] hover:shadow-sm',
        meta.textColor,
        meta.badge,
    ];
}

function formatPercent(score) {
    return `${normalizePercent(score).toFixed(1)}`;
}

function chunkBadgeColor(val) {
    return scoreMeta(val).badge;
}

function chunkLabel(val) {
    return scoreMeta(val).shortLabel;
}

function sentenceTooltip(score, contextScore = props.result) {
    return `Score IA : ${formatPercent(sentenceVisualScore(score, contextScore))}%`;
}

// For single text (no chunks), use the sentences prop directly
const displaySentences = computed(() => {
    if (props.sentences && props.sentences.length > 0) return props.sentences;
    return null;
});

const shareText = computed(() => {
    return `Résultat ReinIA: ${v.value.title}. Score IA ${aiPercent.value}%, Humain ${humanPercent.value}%.`;
});

const shareUrl = computed(() => {
    if (typeof window === 'undefined') return '';
    return window.location.href;
});

const whatsappShareUrl = computed(() => `https://wa.me/?text=${encodeURIComponent(`${shareText.value} ${shareUrl.value}`)}`);
const facebookShareUrl = computed(() => `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl.value)}`);
const emailShareUrl = computed(() => {
    const subject = encodeURIComponent('Résultat d’analyse ReinIA');
    const body = encodeURIComponent(`${shareText.value}\n\n${shareUrl.value}`);
    return `mailto:?subject=${subject}&body=${body}`;
});

const legendItems = computed(() => ([
    { label: 'IA détectée', ...scoreMeta(85) },
    { label: 'Probablement IA', ...scoreMeta(70) },
    { label: 'Incertain', ...scoreMeta(45) },
    { label: 'Humain', ...scoreMeta(15) },
]));

async function copyShareText() {
    try {
        await navigator.clipboard.writeText(`${shareText.value} ${shareUrl.value}`.trim());
        copied.value = true;
        setTimeout(() => {
            copied.value = false;
        }, 2000);
    } catch {
        copied.value = false;
    }
}
</script>

<template>
    <transition enter-active-class="transition duration-400 ease-out" enter-from-class="opacity-0 translate-y-4" enter-to-class="opacity-100 translate-y-0">
        <div class="space-y-4">
            <!-- RESULT CARD with gauge -->
            <div class="rounded-2xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/50 shadow-sm overflow-hidden">
                <div class="px-6 py-4 flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full" :class="v.dot"></span>
                        <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">Résultat de l'analyse</span>
                    </div>
                    <span class="text-xs px-2.5 py-1 rounded-full border border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-500">RoBERTa + Perplexité</span>
                </div>

                <div class="p-6 sm:p-8">
                    <div class="flex flex-col sm:flex-row items-center gap-6 sm:gap-10">
                        <!-- Gauge -->
                        <div class="relative w-48 h-28 shrink-0">
                            <svg viewBox="0 0 200 110" class="w-full h-full">
                                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="currentColor" stroke-width="18" stroke-linecap="round" class="text-slate-100 dark:text-slate-800" />
                                <path d="M 20 100 A 80 80 0 0 1 37.6 42.3" fill="none" stroke="#22c55e" stroke-width="18" stroke-linecap="round" opacity="0.85" />
                                <path d="M 37.6 42.3 A 80 80 0 0 1 100 20" fill="none" stroke="#eab308" stroke-width="18" opacity="0.7" />
                                <path d="M 100 20 A 80 80 0 0 1 162.4 42.3" fill="none" stroke="#f97316" stroke-width="18" opacity="0.7" />
                                <path d="M 162.4 42.3 A 80 80 0 0 1 180 100" fill="none" stroke="#ef4444" stroke-width="18" stroke-linecap="round" opacity="0.85" />
                                <g :transform="`rotate(${needleAngle}, 100, 100)`">
                                    <line x1="100" y1="100" x2="100" y2="30" stroke="#1e293b" stroke-width="3" stroke-linecap="round" class="dark:stroke-white" />
                                </g>
                                <circle cx="100" cy="100" r="8" class="fill-slate-200 dark:fill-slate-700" />
                                <circle cx="100" cy="100" r="5" class="fill-white dark:fill-slate-900" />
                            </svg>
                        </div>

                        <!-- Score + Verdict -->
                        <div class="text-center sm:text-left flex-1">
                            <p class="text-base sm:text-lg font-semibold" :class="v.textColor">{{ v.title }}</p>
                            <p class="text-sm text-slate-400 dark:text-slate-500 mt-0.5 max-w-sm">{{ v.subtitle }}</p>
                            <!-- Two clear percentages -->
                            <div class="flex items-center gap-6 mt-4">
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                                    <span class="text-2xl sm:text-3xl font-black tabular-nums text-emerald-600 dark:text-emerald-400">{{ humanPercent }}%</span>
                                    <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Humain</span>
                                </div>
                                <div class="w-px h-8 bg-slate-200 dark:bg-slate-700"></div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-red-500"></span>
                                    <span class="text-2xl sm:text-3xl font-black tabular-nums text-red-500 dark:text-red-400">{{ aiPercent }}%</span>
                                    <span class="text-sm font-medium text-slate-500 dark:text-slate-400">IA</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Bar -->
                    <div class="mt-6">
                        <div class="mb-1.5 flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-300">
                            <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> Humain</span>
                            <span class="flex items-center gap-1.5">IA <span class="w-2 h-2 rounded-full bg-red-500"></span></span>
                        </div>
                        <div class="w-full h-2.5 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                            <div class="h-full rounded-full transition-all duration-1000 ease-out" :class="authenticityBarColor(humanScore)" :style="{ width: humanScore + '%' }"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- LEGEND -->
            <div class="flex flex-wrap items-center gap-3 px-1 text-xs text-slate-500 dark:text-slate-400">
                <span class="font-medium text-slate-600 dark:text-slate-300">Légende :</span>
                <span
                    v-for="item in legendItems"
                    :key="item.label"
                    class="flex items-center gap-1.5"
                    :class="item.legendText"
                >
                    <span class="h-2.5 w-3 rounded-sm border" :class="item.legendSwatch"></span>
                    {{ item.label }}
                </span>
            </div>

            <!-- SHARE -->
            <div class="rounded-2xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/50 shadow-sm overflow-hidden">
                <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-800/60 flex items-center justify-between gap-3">
                    <div>
                        <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-300">Partager le résultat</h3>
                        <p class="mt-1 text-xs text-slate-400 dark:text-slate-500">Envoyer un résumé par WhatsApp, Facebook, email ou copier le texte.</p>
                    </div>
                    <span v-if="copied" class="text-xs font-medium text-emerald-600 dark:text-emerald-400">Copié</span>
                </div>
                <div class="px-6 py-4 flex flex-wrap gap-2">
                    <a
                        :href="whatsappShareUrl"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                    >
                        <span class="w-2.5 h-2.5 rounded-full bg-green-500"></span>
                        WhatsApp
                    </a>
                    <a
                        :href="facebookShareUrl"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                    >
                        <span class="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                        Facebook
                    </a>
                    <a
                        :href="emailShareUrl"
                        class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                    >
                        <span class="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                        Email
                    </a>
                    <button
                        type="button"
                        class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800 cursor-pointer"
                        @click="copyShareText"
                    >
                        <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                        Copier
                    </button>
                </div>
            </div>

            <!-- SINGLE TEXT SENTENCES (no chunks) -->
            <div v-if="displaySentences && (!chunkResults || chunkResults.length <= 1)" class="rounded-2xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/50 shadow-sm overflow-hidden">
                <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-800/60 flex items-center justify-between">
                    <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-300">Détail phrase par phrase</h3>
                    <span class="text-xs text-slate-400 dark:text-slate-500">{{ displaySentences.length }} phrases</span>
                </div>
                <div class="px-6 py-5">
                    <p class="text-sm leading-8 text-slate-700 dark:text-slate-300">
                        <template v-for="(sent, i) in displaySentences" :key="i">
                            <span class="group/sentence relative inline-block align-baseline">
                                <span
                                    :class="sentenceClasses(sent.score, result)"
                                    :title="sentenceTooltip(sent.score, result)"
                                >{{ sent.text }}</span>
                                <span class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] font-medium text-white opacity-0 shadow-lg transition-opacity duration-150 group-hover/sentence:opacity-100 dark:bg-slate-100 dark:text-slate-900">
                                    IA {{ formatPercent(sentenceVisualScore(sent.score, result)) }}%
                                </span>
                            </span>{{ ' ' }}
                        </template>
                    </p>
                </div>
            </div>

            <!-- CHUNK SECTIONS (multi-section analysis) -->
            <div v-if="chunkResults && chunkResults.length > 1" class="space-y-3">
                <!-- Preprocessing stats -->
                <div v-if="preprocessing" class="rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/50 px-5 py-3">
                    <div class="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 dark:text-slate-400">
                        <span class="flex items-center gap-1">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                            {{ (preprocessing.original_length / 1000).toFixed(1) }}k car. original
                        </span>
                        <span class="flex items-center gap-1">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" /></svg>
                            {{ (preprocessing.cleaned_length / 1000).toFixed(1) }}k car. analysés
                        </span>
                        <span v-if="preprocessing.sections_removed > 0" class="flex items-center gap-1">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" /></svg>
                            {{ preprocessing.sections_removed }} section(s) filtrée(s)
                        </span>
                        <span class="flex items-center gap-1">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6z" /></svg>
                            {{ preprocessing.chunk_count }} chunk(s) analysé(s)
                        </span>
                    </div>
                </div>

                <!-- Section cards -->
                <div v-for="(chunk, i) in chunkResults" :key="i"
                    class="rounded-2xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/50 shadow-sm overflow-hidden"
                >
                    <!-- Section header (always visible) -->
                    <button
                        @click="toggleChunk(i)"
                        class="w-full px-5 py-4 flex items-center gap-4 hover:bg-slate-50/80 dark:hover:bg-slate-800/30 transition-colors text-left"
                    >
                        <svg
                            class="w-4 h-4 text-slate-400 shrink-0 transition-transform duration-200"
                            :class="expandedChunks[i] ? 'rotate-90' : ''"
                            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                        ><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>

                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2">
                                <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">Section {{ i + 1 }}</span>
                                <span class="text-xs text-slate-400 dark:text-slate-500">{{ chunk.label }}</span>
                            </div>
                            <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">{{ chunk.char_count?.toLocaleString() }} caractères</p>
                        </div>

                        <!-- Score badge -->
                        <div class="flex items-center gap-3 shrink-0">
                            <div class="w-20 h-2 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
                                <div class="h-full rounded-full transition-all duration-700" :class="barColor(chunk.ai_probability)" :style="{ width: chunk.ai_probability + '%' }"></div>
                            </div>
                            <span class="text-sm font-bold tabular-nums min-w-[3rem] text-right" :class="scoreMeta(chunk.ai_probability).textColor">
                                {{ Math.round(chunk.ai_probability) }}%
                            </span>
                            <span class="text-[10px] font-medium px-2 py-0.5 rounded-full border" :class="chunkBadgeColor(chunk.ai_probability)">
                                {{ chunkLabel(chunk.ai_probability) }}
                            </span>
                        </div>
                    </button>

                    <!-- Expanded detail -->
                    <transition
                        enter-active-class="transition-all duration-300 ease-out"
                        enter-from-class="max-h-0 opacity-0"
                        enter-to-class="max-h-[2000px] opacity-100"
                        leave-active-class="transition-all duration-200 ease-in"
                        leave-from-class="max-h-[2000px] opacity-100"
                        leave-to-class="max-h-0 opacity-0"
                    >
                        <div v-if="expandedChunks[i]" class="overflow-hidden">
                            <!-- Scores detail -->
                            <div class="px-5 py-3 border-t border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-800/20 flex flex-wrap gap-4 text-xs">
                                <span class="text-slate-500 dark:text-slate-400">
                                    RoBERTa : <span class="font-semibold text-slate-700 dark:text-slate-300">{{ (chunk.score_roberta * 100).toFixed(1) }}%</span>
                                </span>
                                <span class="text-slate-500 dark:text-slate-400">
                                    Perplexité : <span class="font-semibold text-slate-700 dark:text-slate-300">{{ (chunk.score_ppl * 100).toFixed(1) }}%</span>
                                </span>
                                <span class="text-slate-500 dark:text-slate-400">
                                    Score final : <span class="font-bold" :class="scoreMeta(chunk.ai_probability).textColor">{{ chunk.ai_probability.toFixed(1) }}%</span>
                                </span>
                            </div>

                            <!-- Colored text -->
                            <div class="px-5 py-5 border-t border-slate-100 dark:border-slate-800/60">
                                <p v-if="chunk.sentences && chunk.sentences.length > 0" class="text-sm leading-8 text-slate-700 dark:text-slate-300">
                                    <template v-for="(sent, j) in chunk.sentences" :key="j">
                                        <span class="group/sentence relative inline-block align-baseline">
                                            <span
                                                :class="sentenceClasses(sent.score, chunk.ai_probability)"
                                                :title="sentenceTooltip(sent.score, chunk.ai_probability)"
                                            >{{ sent.text }}</span>
                                            <span class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] font-medium text-white opacity-0 shadow-lg transition-opacity duration-150 group-hover/sentence:opacity-100 dark:bg-slate-100 dark:text-slate-900">
                                                IA {{ formatPercent(sentenceVisualScore(sent.score, chunk.ai_probability)) }}%
                                            </span>
                                        </span>{{ ' ' }}
                                    </template>
                                </p>
                                <p v-else-if="chunk.text" class="text-sm leading-7 text-slate-600 dark:text-slate-400 whitespace-pre-line">{{ chunk.text }}</p>
                                <p v-else class="text-sm text-slate-400 italic">Texte non disponible</p>
                            </div>
                        </div>
                    </transition>
                </div>
            </div>
        </div>
    </transition>
</template>
