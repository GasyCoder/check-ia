<script setup>
/**
 * HumanizePanel — Full humanization panel with intensity selector,
 * streaming display, diff viewer, and score comparison.
 */
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import ScoreGauge from './ScoreGauge.vue';
import DiffViewer from './DiffViewer.vue';
import { useToast } from '../Composables/useToast';

const props = defineProps({
    originalText: { type: String, required: true },
    originalScore: { type: Number, default: 0 },
    sentences: { type: Array, default: () => [] },
    initialIntensity: { type: String, default: 'medium' },
    initialHumanizedText: { type: String, default: '' },
    initialResponseSegments: { type: Array, default: () => [] },
    initialHumanizedScore: { type: Number, default: null },
});

const emit = defineEmits(['close']);
const toast = useToast();

const intensity = ref('medium');
const humanizedText = ref('');
const humanizedSegments = ref([]);
const humanizedScore = ref(null);
const isHumanizing = ref(false);
const isReanalyzing = ref(false);
const reanalyzeProgress = ref(0);
const copied = ref(false);
const showDiff = ref(true);

const intensityOptions = [
    {
        value: 'light',
        label: 'Léger',
        description: 'Modifications subtiles, conserve le style original',
        iconPath: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z',
    },
    {
        value: 'medium',
        label: 'Moyen',
        description: 'Équilibre entre naturalité et fidélité au sens',
        iconPath: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z',
    },
    {
        value: 'aggressive',
        label: 'Agressif',
        description: 'Réécriture profonde, style très différent',
        iconPath: 'M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z',
    },
];

function normalizeWhitespace(value) {
    return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function normalizePercent(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? Math.max(0, Math.min(100, numeric)) : 0;
}

const sourceSegments = computed(() => Array.isArray(props.sentences) ? props.sentences : []);
const originalHumanScore = computed(() => Math.max(0, 100 - normalizePercent(props.originalScore)));
const humanizedHumanScore = computed(() => {
    if (humanizedScore.value === null) return null;
    return Math.max(0, 100 - normalizePercent(humanizedScore.value));
});
const scoreDelta = computed(() => {
    if (humanizedScore.value === null) return null;
    return normalizePercent(humanizedScore.value) - normalizePercent(props.originalScore);
});
const humanDelta = computed(() => {
    if (humanizedHumanScore.value === null) return null;
    return humanizedHumanScore.value - originalHumanScore.value;
});
const comparisonState = computed(() => {
    if (scoreDelta.value === null) return null;

    if (scoreDelta.value <= -1) {
        return {
            tone: 'success',
            title: 'Amelioration nette',
            message: `Detection IA : ${scoreDelta.value.toFixed(1)} points. Authenticite : +${Math.abs(humanDelta.value ?? 0).toFixed(1)} points.`,
            classes: 'text-emerald-600 dark:text-emerald-400',
            icon: 'M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941',
        };
    }

    if (scoreDelta.value < 1) {
        const iaPrefix = scoreDelta.value >= 0 ? '+' : '';
        const humanPrefix = (humanDelta.value ?? 0) >= 0 ? '+' : '';

        return {
            tone: 'neutral',
            title: 'Resultat quasi inchange',
            message: `Detection IA : ${iaPrefix}${scoreDelta.value.toFixed(1)} point. Authenticite : ${humanPrefix}${(humanDelta.value ?? 0).toFixed(1)} point.`,
            classes: 'text-zinc-500 dark:text-zinc-400',
            icon: 'M5.25 12h13.5',
        };
    }

    return {
        tone: 'warning',
        title: 'Resultat moins bon',
        message: `Detection IA : +${scoreDelta.value.toFixed(1)} points. Authenticite : ${(humanDelta.value ?? 0).toFixed(1)} points.`,
        classes: 'text-rose-600 dark:text-rose-400',
        icon: 'M17.25 6.75L6.75 17.25M6.75 6.75l10.5 10.5',
    };
});
const activeStatus = computed(() => {
    if (isHumanizing.value) {
        return {
            title: 'Humanisation en cours...',
            description: 'Réécriture du texte et préparation du diff phrase par phrase.',
            accent: 'border-purple-200 bg-purple-50 text-purple-700 dark:border-purple-500/20 dark:bg-purple-500/10 dark:text-purple-300',
            spinner: 'border-purple-300 border-t-purple-600',
        };
    }

    if (isReanalyzing.value) {
        return {
            title: 'Re-analyse en cours...',
            description: 'Calcul du nouveau score IA sur le texte humanisé.',
            accent: 'border-indigo-200 bg-indigo-50 text-indigo-700 dark:border-indigo-500/20 dark:bg-indigo-500/10 dark:text-indigo-300',
            spinner: 'border-indigo-300 border-t-indigo-600',
        };
    }

    return null;
});

const finalHumanizedText = computed(() => {
    if (humanizedSegments.value.length > 0) {
        return humanizedSegments.value
            .map((segment) => `${segment.modified}${segment.separator ?? ''}`)
            .join('');
    }

    return humanizedText.value;
});

const hasResult = computed(() => finalHumanizedText.value.length > 0);

function resetHumanization() {
    humanizedText.value = '';
    humanizedSegments.value = [];
    humanizedScore.value = null;
}

function resolveIntensity(value) {
    return intensityOptions.some((option) => option.value === value) ? value : 'medium';
}

function buildMappedSegments(responseSegments = []) {
    if (!sourceSegments.value.length || !Array.isArray(responseSegments) || responseSegments.length === 0) {
        return [];
    }

    const responseById = new Map(
        responseSegments.map((segment, index) => [String(segment?.id ?? index), segment]),
    );

    return sourceSegments.value.map((segment, index) => {
        const responseSegment = responseById.get(String(segment.id)) ?? responseSegments[index] ?? null;
        const modifiedText = String(responseSegment?.humanized_text ?? segment.text ?? '');

        return {
            id: segment.id ?? `sentence-${index}`,
            order: segment.order ?? index,
            score: segment.score ?? null,
            separator: segment.separator ?? (index < sourceSegments.value.length - 1 ? ' ' : ''),
            original: segment.text,
            modified: modifiedText,
            changed: normalizeWhitespace(modifiedText) !== normalizeWhitespace(segment.text),
        };
    });
}

function syncInitialState() {
    intensity.value = resolveIntensity(props.initialIntensity);
    humanizedText.value = props.initialHumanizedText || '';
    humanizedSegments.value = buildMappedSegments(props.initialResponseSegments);

    const numericScore = Number(props.initialHumanizedScore);
    humanizedScore.value = Number.isFinite(numericScore) ? normalizePercent(numericScore) : null;
}

watch(
    () => [
        props.initialIntensity,
        props.initialHumanizedText,
        props.initialHumanizedScore,
        props.initialResponseSegments,
        props.sentences,
        props.originalText,
    ],
    syncInitialState,
    { immediate: true, deep: true },
);

async function selectIntensity(value) {
    if (intensity.value === value) return;

    intensity.value = value;
    humanizedScore.value = null;

    if (!hasResult.value || isHumanizing.value || isReanalyzing.value) {
        return;
    }

    await humanize();
}

async function humanize() {
    if (isHumanizing.value) return;
    isHumanizing.value = true;
    resetHumanization();

    try {
        const segments = sourceSegments.value.map((segment) => ({
            id: segment.id,
            text: segment.text,
        }));

        const res = await axios.post('/humanize', {
            text: props.originalText,
            intensity: intensity.value,
            mode: 'manual-humanize',
            segments,
        }, { timeout: 120000 });

        humanizedText.value = res.data.humanized_text || '';
        humanizedSegments.value = buildMappedSegments(res.data.segments);

        toast.success('Texte humanisé avec succès');
    } catch (err) {
        const msg = err.response?.data?.error || 'Erreur lors de l\'humanisation.';
        toast.error(msg);
    } finally {
        isHumanizing.value = false;
    }
}

async function reanalyze() {
    if (isReanalyzing.value || !finalHumanizedText.value) return;
    isReanalyzing.value = true;
    reanalyzeProgress.value = 0;

    const interval = setInterval(() => {
        if (reanalyzeProgress.value < 90) {
            reanalyzeProgress.value += Math.random() * 15;
            if (reanalyzeProgress.value > 90) reanalyzeProgress.value = 90;
        }
    }, 500);

    try {
        const res = await axios.post('/analyze-text', { text: finalHumanizedText.value, mode: 'detect' }, { timeout: 300000 });
        reanalyzeProgress.value = 100;
        clearInterval(interval);
        await new Promise(r => setTimeout(r, 400)); // Laisse le temps à l'utilisateur de voir 100%

        const raw = Number(res.data.result);
        humanizedScore.value = raw >= 0 && raw <= 1 ? raw * 100 : Math.max(0, Math.min(100, raw));
        toast.success('Re-analyse terminée');
    } catch {
        clearInterval(interval);
        toast.error('Erreur lors de la re-analyse.');
    } finally {
        isReanalyzing.value = false;
    }
}

async function copyText() {
    try {
        await navigator.clipboard.writeText(finalHumanizedText.value);
        copied.value = true;
        toast.success('Texte copié dans le presse-papier');
        setTimeout(() => { copied.value = false; }, 2000);
    } catch {
        toast.error('Impossible de copier le texte.');
    }
}

function downloadText() {
    const blob = new Blob([finalHumanizedText.value], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'texte-humanise.txt';
    a.click();
    URL.revokeObjectURL(url);
}
</script>

<template>
    <div class="animate-slide-up space-y-5">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg shadow-purple-500/20">
                    <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" /></svg>
                </div>
                <div>
                    <h2 class="font-display text-lg font-bold text-zinc-900 dark:text-zinc-100">Humanisation</h2>
                    <p class="text-xs text-zinc-500 dark:text-zinc-400">Réécrire le texte pour réduire la détection IA</p>
                </div>
            </div>
        </div>

        <div
            v-if="activeStatus"
            class="flex items-start gap-3 rounded-xl border px-4 py-3"
            :class="activeStatus.accent"
        >
            <div class="mt-0.5 h-4 w-4 animate-spin rounded-full border-2" :class="activeStatus.spinner"></div>
            <div>
                <p class="text-sm font-semibold">{{ activeStatus.title }}</p>
                <p class="text-xs opacity-90">{{ activeStatus.description }}</p>
            </div>
        </div>

        <!-- Intensity selector -->
        <div class="grid gap-3 sm:grid-cols-3">
            <button
                v-for="opt in intensityOptions"
                :key="opt.value"
                type="button"
                class="group rounded-xl border-2 p-4 text-left transition-all duration-200 cursor-pointer"
                :class="intensity === opt.value
                    ? 'border-purple-500 bg-purple-50 dark:border-purple-400 dark:bg-purple-500/10'
                    : 'border-zinc-200 hover:border-zinc-300 dark:border-zinc-700 dark:hover:border-zinc-600'"
                @click="selectIntensity(opt.value)"
            >
                <div class="flex items-center gap-2">
                    <span class="flex h-6 w-6 items-center justify-center rounded-full" :class="intensity === opt.value ? 'bg-purple-100 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400' : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400'">
                        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                            <path stroke-linecap="round" stroke-linejoin="round" :d="opt.iconPath" />
                        </svg>
                    </span>
                    <span class="text-sm font-semibold" :class="intensity === opt.value ? 'text-purple-700 dark:text-purple-300' : 'text-zinc-700 dark:text-zinc-300'">{{ opt.label }}</span>
                </div>
                <p class="mt-1 text-xs" :class="intensity === opt.value ? 'text-purple-600 dark:text-purple-400' : 'text-zinc-500 dark:text-zinc-400'">{{ opt.description }}</p>
            </button>
        </div>

        <!-- Humanize button -->
        <div v-if="!hasResult" class="flex justify-end">
            <button
                type="button"
                :disabled="isHumanizing"
                class="group flex items-center justify-center gap-2 rounded-xl px-7 py-3 text-sm font-semibold transition-all duration-300 cursor-pointer disabled:cursor-not-allowed"
                :class="isHumanizing
                    ? 'bg-purple-100 text-purple-400 dark:bg-purple-500/10 dark:text-purple-500'
                    : 'bg-purple-600 text-white shadow-lg shadow-purple-500/20 hover:bg-purple-500 hover:shadow-xl hover:shadow-purple-500/30'"
                @click="humanize"
            >
                <template v-if="isHumanizing">
                    <div class="h-4 w-4 animate-spin rounded-full border-2 border-purple-300 border-t-purple-600"></div>
                    Humanisation en cours...
                </template>
                <template v-else>
                    <svg class="h-4 w-4 transition-transform duration-200 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" /></svg>
                    Humaniser le texte
                </template>
            </button>
        </div>

        <!-- Results -->
        <template v-if="hasResult">
            <!-- Score comparison -->
            <div class="overflow-hidden rounded-xl border border-zinc-200/60 bg-white shadow-sm dark:border-zinc-800/60 dark:bg-zinc-900/80">
                <div class="border-b border-zinc-100 bg-zinc-50/50 px-5 py-3 dark:border-zinc-800 dark:bg-zinc-800/30">
                    <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Comparaison des scores</h3>
                    <p class="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                        Plus le score de détection IA baisse, plus l’authenticité estimée du texte augmente.
                    </p>
                </div>
                <div class="grid gap-6 p-6 sm:grid-cols-2">
                    <div class="flex flex-col items-center gap-3 text-center">
                        <ScoreGauge :score="originalScore" label="Détection IA initiale" size="md" palette="cyan" />
                        <div class="flex flex-wrap items-center justify-center gap-2 text-xs">
                            <span class="rounded-full border border-cyan-200 bg-cyan-50 px-2.5 py-1 font-medium text-cyan-700 dark:border-cyan-500/20 dark:bg-cyan-500/10 dark:text-cyan-300">
                                IA : {{ normalizePercent(originalScore).toFixed(1) }}%
                            </span>
                            <span class="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                                Authenticité : {{ originalHumanScore.toFixed(1) }}%
                            </span>
                        </div>
                    </div>
                    <div class="flex flex-col items-center gap-3 text-center">
                        <template v-if="humanizedScore !== null">
                            <ScoreGauge :score="humanizedScore" label="Détection IA après humanisation" size="md" palette="violet" />
                            <div class="flex flex-wrap items-center justify-center gap-2 text-xs">
                                <span class="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 font-medium text-violet-700 dark:border-violet-500/20 dark:bg-violet-500/10 dark:text-violet-300">
                                    IA : {{ normalizePercent(humanizedScore).toFixed(1) }}%
                                </span>
                                <span class="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                                    Authenticité : {{ humanizedHumanScore?.toFixed(1) }}%
                                </span>
                            </div>
                        </template>
                        <template v-else>
                            <div class="flex flex-col items-center gap-3">
                                <div v-if="isReanalyzing" class="relative flex h-[136px] w-[136px] items-center justify-center rounded-full border-4 border-zinc-100 dark:border-zinc-800">
                                    <svg class="absolute inset-0 h-full w-full -rotate-90" viewBox="0 0 100 100">
                                        <circle cx="50" cy="50" r="46" fill="none" class="stroke-indigo-500 transition-all duration-300" stroke-width="8" :stroke-dasharray="289" :stroke-dashoffset="289 - (289 * reanalyzeProgress) / 100" stroke-linecap="round" />
                                    </svg>
                                    <span class="font-display text-2xl font-bold tabular-nums text-indigo-600 dark:text-indigo-400">{{ Math.round(reanalyzeProgress) }}<span class="text-xs">%</span></span>
                                </div>
                                <div v-else class="flex h-[136px] w-[136px] items-center justify-center rounded-full border-2 border-dashed border-zinc-200 dark:border-zinc-700">
                                    <span class="text-sm text-zinc-400 dark:text-zinc-500">?</span>
                                </div>
                                <div v-if="isReanalyzing" class="space-y-1 text-center">
                                    <p class="text-sm font-semibold text-indigo-600 dark:text-indigo-400">Re-analyse en cours...</p>
                                    <p class="text-xs text-zinc-500 dark:text-zinc-400">Le score IA est en train d’être recalculé.</p>
                                </div>
                                <div v-else class="space-y-1 text-center">
                                    <p class="text-sm font-semibold text-zinc-700 dark:text-zinc-300">Score après humanisation</p>
                                    <p class="text-xs text-zinc-500 dark:text-zinc-400">Lancez la re-analyse pour voir la nouvelle détection IA et l’authenticité estimée.</p>
                                </div>
                                <button
                                    v-if="!isReanalyzing"
                                    type="button"
                                    class="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 cursor-pointer"
                                    @click="reanalyze"
                                >
                                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" /></svg>
                                    Re-analyser
                                </button>
                            </div>
                        </template>
                    </div>
                </div>

                <!-- Improvement banner -->
                <div v-if="comparisonState" class="border-t border-zinc-100 px-5 py-3 dark:border-zinc-800">
                    <div class="flex items-center gap-2 text-sm font-medium" :class="comparisonState.classes">
                        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" :d="comparisonState.icon" />
                        </svg>
                        {{ comparisonState.title }}. {{ comparisonState.message }}
                    </div>
                </div>
            </div>

            <!-- Diff / Text toggle -->
            <div class="flex items-center gap-2">
                <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer"
                    :class="showDiff ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900' : 'text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800'"
                    @click="showDiff = true"
                >
                    Diff
                </button>
                <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer"
                    :class="!showDiff ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900' : 'text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800'"
                    @click="showDiff = false"
                >
                    Texte final
                </button>
            </div>

            <!-- Diff viewer -->
            <DiffViewer
                v-if="showDiff"
                :original="originalText"
                :modified="finalHumanizedText"
                :segments="humanizedSegments"
            />

            <!-- Plain text view -->
            <div v-else class="rounded-xl border border-zinc-200/60 bg-white p-5 dark:border-zinc-800/60 dark:bg-zinc-900/80">
                <p class="whitespace-pre-line text-sm leading-7 text-zinc-700 dark:text-zinc-200">{{ finalHumanizedText }}</p>
            </div>

            <!-- Actions -->
            <div class="flex flex-wrap items-center gap-3">
                <button type="button" @click="copyText" class="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 cursor-pointer">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" /></svg>
                    {{ copied ? '✓ Copié' : 'Copier le texte' }}
                </button>
                <button type="button" @click="downloadText" class="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 cursor-pointer">
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
                    Télécharger .txt
                </button>
                <button
                    type="button"
                    class="flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-purple-500 cursor-pointer"
                    @click="resetHumanization(); humanize()"
                >
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" /></svg>
                    Ré-humaniser
                </button>
            </div>
        </template>
    </div>
</template>
