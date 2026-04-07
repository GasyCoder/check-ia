<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
    result: { type: Number, required: true },
    chunkResults: { type: Array, default: null },
    sentences: { type: Array, default: null },
    preprocessing: { type: Object, default: null },
});

const activeTab = ref('overview');
const expandedChunks = ref({});
const copied = ref(false);

function normalizePercent(value) {
    const numeric = Number(value);

    if (!Number.isFinite(numeric)) return 0;

    if (numeric >= 0 && numeric <= 1) {
        return Math.min(100, Math.max(0, numeric * 100));
    }

    return Math.min(100, Math.max(0, numeric));
}

const aiScore = computed(() => normalizePercent(props.result));
const humanScore = computed(() => Math.max(0, 100 - aiScore.value));
const humanPercent = computed(() => humanScore.value.toFixed(1));
const aiPercent = computed(() => aiScore.value.toFixed(1));
const hasSections = computed(() => Array.isArray(props.chunkResults) && props.chunkResults.length > 1);
const displaySentences = computed(() => {
    if (props.sentences && props.sentences.length > 0) return props.sentences;
    return null;
});

const availableTabs = computed(() => {
    const tabs = [{ key: 'overview', label: 'Overview' }];

    if (displaySentences.value?.length) {
        tabs.push({ key: 'phrases', label: 'Phrases' });
    }

    if (hasSections.value) {
        tabs.push({ key: 'sections', label: 'Sections' });
    }

    return tabs;
});

function toggleChunk(index) {
    expandedChunks.value[index] = !expandedChunks.value[index];
}

function verdictMeta(score) {
    const value = normalizePercent(score);

    if (value >= 80) {
        return {
            title: 'IA détectée',
            subtitle: 'Le document présente un signal très fort de génération artificielle.',
            badge: 'bg-rose-50 text-rose-700 border-rose-200',
            accent: 'text-rose-600',
        };
    }

    if (value >= 60) {
        return {
            title: 'Probablement IA',
            subtitle: 'Le texte reste très structuré et présente plusieurs marqueurs typiques.',
            badge: 'bg-amber-50 text-amber-700 border-amber-200',
            accent: 'text-amber-600',
        };
    }

    if (value >= 30) {
        return {
            title: 'Incertain',
            subtitle: 'Le résultat mélange des indices humains et artificiels.',
            badge: 'bg-zinc-100 text-zinc-700 border-zinc-200',
            accent: 'text-zinc-700',
        };
    }

    return {
        title: 'Très probablement humain',
        subtitle: 'Le document conserve une structure et une variation proches d’un texte authentique.',
        badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        accent: 'text-emerald-600',
    };
}

const verdict = computed(() => verdictMeta(props.result));

function authenticityBarColor(value) {
    const percent = normalizePercent(value);

    if (percent > 60) return 'bg-emerald-500';
    if (percent >= 40) return 'bg-amber-400';
    return 'bg-rose-500';
}

function sentenceClasses(score) {
    const value = normalizePercent(score);

    if (value >= 75) {
        return 'rounded-md border border-rose-300 bg-rose-500/20 px-2 py-1 text-zinc-800 transition-colors dark:border-rose-500/30 dark:bg-rose-500/25 dark:text-zinc-100';
    }

    if (value >= 50) {
        return 'rounded-md border border-rose-200 bg-rose-500/10 px-2 py-1 text-zinc-800 transition-colors dark:border-rose-500/20 dark:bg-rose-500/15 dark:text-zinc-100';
    }

    if (value >= 25) {
        return 'rounded-md border border-emerald-200 bg-emerald-500/10 px-2 py-1 text-zinc-800 transition-colors dark:border-emerald-500/15 dark:bg-emerald-500/10 dark:text-zinc-100';
    }

    return 'rounded-md border border-emerald-300 bg-emerald-500/20 px-2 py-1 text-zinc-800 transition-colors dark:border-emerald-500/25 dark:bg-emerald-500/20 dark:text-zinc-100';
}

function sentenceTooltip(score) {
    const value = normalizePercent(score);
    return value >= 50 ? `IA : ${value.toFixed(1)}%` : `Humain : ${(100 - value).toFixed(1)}%`;
}

function chunkVerdict(score) {
    return verdictMeta(score).title;
}

const shareText = computed(() => `Résultat ReinIA: ${verdict.value.title}. Score IA ${aiPercent.value}%, Humain ${humanPercent.value}%.`);
const shareUrl = computed(() => (typeof window === 'undefined' ? '' : window.location.href));
const whatsappShareUrl = computed(() => `https://wa.me/?text=${encodeURIComponent(`${shareText.value} ${shareUrl.value}`)}`);
const emailShareUrl = computed(() => {
    const subject = encodeURIComponent('Résultat d’analyse ReinIA');
    const body = encodeURIComponent(`${shareText.value}\n\n${shareUrl.value}`);
    return `mailto:?subject=${subject}&body=${body}`;
});

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
    <div class="space-y-6">
        <div class="border-b border-zinc-200 dark:border-zinc-800">
            <nav class="-mb-px flex items-center gap-6">
                <button
                    v-for="tab in availableTabs"
                    :key="tab.key"
                    type="button"
                    class="border-b-2 px-1 pb-3 text-sm font-medium transition-colors cursor-pointer"
                    :class="activeTab === tab.key ? 'border-blue-600 text-zinc-950 dark:text-zinc-50' : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200'"
                    @click="activeTab = tab.key"
                >
                    {{ tab.label }}
                </button>
            </nav>
        </div>

        <div v-if="activeTab === 'overview'" class="space-y-6">
            <section class="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/90 sm:p-8">
                <div class="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
                    <div class="space-y-5">
                        <div class="space-y-2">
                            <p class="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Detection summary</p>
                            <div class="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium" :class="verdict.badge">
                                {{ verdict.title }}
                            </div>
                            <p class="max-w-2xl text-sm text-zinc-500 dark:text-zinc-400">{{ verdict.subtitle }}</p>
                        </div>

                        <div class="grid gap-4 sm:grid-cols-3">
                            <div class="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
                                <p class="text-sm text-zinc-500 dark:text-zinc-400">Authenticité</p>
                                <p class="mt-2 text-2xl font-semibold text-zinc-950 dark:text-zinc-50">{{ humanPercent }}%</p>
                            </div>
                            <div class="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
                                <p class="text-sm text-zinc-500 dark:text-zinc-400">Détection IA</p>
                                <p class="mt-2 text-2xl font-semibold text-zinc-950 dark:text-zinc-50">{{ aiPercent }}%</p>
                            </div>
                            <div class="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
                                <p class="text-sm text-zinc-500 dark:text-zinc-400">Verdict</p>
                                <p class="mt-2 text-sm font-semibold" :class="verdict.accent">{{ verdict.title }}</p>
                            </div>
                        </div>

                        <div class="space-y-2">
                            <div class="flex items-center justify-between text-sm">
                                <span class="font-medium text-zinc-950 dark:text-zinc-50">Authenticity score</span>
                                <span class="text-zinc-500 dark:text-zinc-400">{{ humanPercent }}%</span>
                            </div>
                            <div class="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                                <div class="h-full rounded-full transition-all duration-700" :class="authenticityBarColor(humanScore)" :style="{ width: `${humanScore}%` }"></div>
                            </div>
                            <div class="flex items-center justify-between text-sm text-zinc-500 dark:text-zinc-400">
                                <span>Faible</span>
                                <span>Élevé</span>
                            </div>
                        </div>
                    </div>

                    <div class="rounded-lg border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-950">
                        <p class="text-sm text-zinc-500 dark:text-zinc-400">Human score</p>
                        <div class="mt-4 flex items-end gap-3">
                            <span class="text-5xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">{{ humanPercent }}</span>
                            <span class="pb-2 text-sm text-zinc-500 dark:text-zinc-400">%</span>
                        </div>
                        <p class="mt-4 text-sm text-zinc-500 dark:text-zinc-400">
                            Lecture simplifiée du niveau d’authenticité du document après agrégation des signaux.
                        </p>

                        <div class="mt-6 space-y-3 border-t border-zinc-200 pt-5 dark:border-zinc-800">
                            <a :href="whatsappShareUrl" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800">
                                <span>Partager sur WhatsApp</span>
                                <span class="text-zinc-400 dark:text-zinc-500">↗</span>
                            </a>
                            <a :href="emailShareUrl" class="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800">
                                <span>Envoyer par email</span>
                                <span class="text-zinc-400 dark:text-zinc-500">↗</span>
                            </a>
                            <button type="button" class="flex w-full items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800 cursor-pointer" @click="copyShareText">
                                <span>{{ copied ? 'Lien copié' : 'Copier le résumé' }}</span>
                                <span class="text-zinc-400 dark:text-zinc-500">⎘</span>
                            </button>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        <section v-if="activeTab === 'phrases' && displaySentences" class="rounded-lg border border-zinc-200 bg-zinc-50 p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950 sm:p-8">
            <div class="mb-5 space-y-3">
                <div class="flex items-center justify-between gap-3">
                    <div>
                        <h3 class="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Détail phrase par phrase</h3>
                        <p class="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Chaque phrase est colorée selon sa probabilité d'origine.</p>
                    </div>
                    <span class="rounded-full border border-zinc-200 bg-white px-3 py-1 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">{{ displaySentences.length }} phrases</span>
                </div>
                <div class="flex items-center gap-4 text-xs text-zinc-500 dark:text-zinc-400">
                    <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-sm border border-emerald-200 bg-emerald-500/20"></span> Humain</span>
                    <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-sm border border-rose-200 bg-rose-500/20"></span> IA</span>
                </div>
            </div>

            <div class="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
                <p class="text-sm leading-8 text-zinc-700 dark:text-zinc-200">
                    <template v-for="(sentence, index) in displaySentences" :key="index">
                        <span class="group relative inline-block align-baseline">
                            <span :class="sentenceClasses(sentence.score)" :title="sentenceTooltip(sentence.score)">{{ sentence.text }}</span>
                            <span class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-zinc-950 px-2 py-1 text-xs font-medium text-white opacity-0 shadow-sm transition-opacity group-hover:opacity-100 dark:bg-zinc-100 dark:text-zinc-900">
                                {{ sentenceTooltip(sentence.score) }}
                            </span>
                        </span>{{ ' ' }}
                    </template>
                </p>
            </div>
        </section>

        <div v-if="activeTab === 'sections' && hasSections" class="space-y-4">
            <div v-if="preprocessing" class="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/90">
                <div class="grid gap-3 text-sm text-zinc-500 dark:text-zinc-400 sm:grid-cols-2 xl:grid-cols-4">
                    <div class="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
                        <p class="text-sm text-zinc-500 dark:text-zinc-400">Original</p>
                        <p class="mt-1 font-semibold text-zinc-950 dark:text-zinc-50">{{ (preprocessing.original_length / 1000).toFixed(1) }}k caractères</p>
                    </div>
                    <div class="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
                        <p class="text-sm text-zinc-500 dark:text-zinc-400">Analysé</p>
                        <p class="mt-1 font-semibold text-zinc-950 dark:text-zinc-50">{{ (preprocessing.cleaned_length / 1000).toFixed(1) }}k caractères</p>
                    </div>
                    <div class="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
                        <p class="text-sm text-zinc-500 dark:text-zinc-400">Sections filtrées</p>
                        <p class="mt-1 font-semibold text-zinc-950 dark:text-zinc-50">{{ preprocessing.sections_removed || 0 }}</p>
                    </div>
                    <div class="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
                        <p class="text-sm text-zinc-500 dark:text-zinc-400">Chunks analysés</p>
                        <p class="mt-1 font-semibold text-zinc-950 dark:text-zinc-50">{{ preprocessing.chunk_count || chunkResults.length }}</p>
                    </div>
                </div>
            </div>

            <div
                v-for="(chunk, index) in chunkResults"
                :key="index"
                class="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900/90"
            >
                <button
                    type="button"
                    class="flex w-full items-center gap-4 px-5 py-4 text-left transition hover:bg-zinc-50 dark:hover:bg-zinc-900 cursor-pointer"
                    @click="toggleChunk(index)"
                >
                    <div class="flex-1">
                        <div class="flex flex-wrap items-center gap-2">
                            <p class="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Section {{ index + 1 }}</p>
                            <span class="text-sm text-zinc-500 dark:text-zinc-400">{{ chunk.label }}</span>
                        </div>
                        <p class="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{{ chunk.char_count?.toLocaleString() }} caractères</p>
                    </div>

                    <div class="w-28">
                        <div class="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div class="h-full rounded-full transition-all duration-500" :class="authenticityBarColor(100 - normalizePercent(chunk.ai_probability))" :style="{ width: `${100 - normalizePercent(chunk.ai_probability)}%` }"></div>
                        </div>
                    </div>

                    <div class="text-right">
                        <p class="text-sm font-semibold text-zinc-950 dark:text-zinc-50">{{ (100 - normalizePercent(chunk.ai_probability)).toFixed(1) }}%</p>
                        <p class="text-sm text-zinc-500 dark:text-zinc-400">{{ chunkVerdict(chunk.ai_probability) }}</p>
                    </div>
                </button>

                <div v-if="expandedChunks[index]" class="border-t border-zinc-200 bg-zinc-50 px-5 py-5 dark:border-zinc-800 dark:bg-zinc-950">
                    <div class="mb-4 grid gap-3 sm:grid-cols-3">
                        <div class="rounded-lg border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                            <p class="text-sm text-zinc-500 dark:text-zinc-400">RoBERTa</p>
                            <p class="mt-1 font-semibold text-zinc-950 dark:text-zinc-50">{{ ((chunk.score_roberta || 0) * 100).toFixed(1) }}%</p>
                        </div>
                        <div class="rounded-lg border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                            <p class="text-sm text-zinc-500 dark:text-zinc-400">Perplexité</p>
                            <p class="mt-1 font-semibold text-zinc-950 dark:text-zinc-50">{{ ((chunk.score_ppl || 0) * 100).toFixed(1) }}%</p>
                        </div>
                        <div class="rounded-lg border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                            <p class="text-sm text-zinc-500 dark:text-zinc-400">Détection IA</p>
                            <p class="mt-1 font-semibold text-zinc-950 dark:text-zinc-50">{{ normalizePercent(chunk.ai_probability).toFixed(1) }}%</p>
                        </div>
                    </div>

                    <div v-if="chunk.sentences?.length" class="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
                        <p class="text-sm leading-8 text-zinc-700 dark:text-zinc-200">
                            <template v-for="(sentence, sentenceIndex) in chunk.sentences" :key="sentenceIndex">
                                <span class="group relative inline-block align-baseline">
                                    <span :class="sentenceClasses(sentence.score)" :title="sentenceTooltip(sentence.score)">{{ sentence.text }}</span>
                                    <span class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-zinc-950 px-2 py-1 text-xs font-medium text-white opacity-0 shadow-sm transition-opacity group-hover:opacity-100 dark:bg-zinc-100 dark:text-zinc-900">
                                        {{ sentenceTooltip(sentence.score) }}
                                    </span>
                                </span>{{ ' ' }}
                            </template>
                        </p>
                    </div>
                    <p v-else class="whitespace-pre-line text-sm leading-7 text-zinc-600 dark:text-zinc-300">{{ chunk.text }}</p>
                </div>
            </div>
        </div>
    </div>
</template>
