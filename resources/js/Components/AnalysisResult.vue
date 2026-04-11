<script setup>
/**
 * AnalysisResult — Premium analysis result display with ScoreGauge,
 * animated cards, sentence highlighting, and humanize trigger.
 */
import { computed, ref, watch } from 'vue';
import ScoreGauge from './ScoreGauge.vue';

const props = defineProps({
    result: { type: Number, required: true },
    chunkResults: { type: Array, default: null },
    sentences: { type: Array, default: null },
    preprocessing: { type: Object, default: null },
    canHumanize: { type: Boolean, default: false },
    initialTab: { type: String, default: 'overview' },
});

const emit = defineEmits(['humanize']);

const activeTab = ref('overview');
const expandedChunks = ref({});
const copied = ref(false);

function normalizePercent(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return 0;
    if (numeric >= 0 && numeric <= 1) return Math.min(100, Math.max(0, numeric * 100));
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
    const tabs = [{ key: 'overview', label: 'Vue d\'ensemble', icon: 'M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z' }];

    if (displaySentences.value?.length) {
        tabs.push({ key: 'phrases', label: 'Phrases', icon: 'M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z' });
    }

    if (hasSections.value) {
        tabs.push({ key: 'sections', label: 'Sections', icon: 'M2.25 7.125C2.25 6.504 2.754 6 3.375 6h6c.621 0 1.125.504 1.125 1.125v3.75c0 .621-.504 1.125-1.125 1.125h-6a1.125 1.125 0 01-1.125-1.125v-3.75zM14.25 8.625c0-.621.504-1.125 1.125-1.125h5.25c.621 0 1.125.504 1.125 1.125v8.25c0 .621-.504 1.125-1.125 1.125h-5.25a1.125 1.125 0 01-1.125-1.125v-8.25zM3.75 16.125c0-.621.504-1.125 1.125-1.125h5.25c.621 0 1.125.504 1.125 1.125v2.25c0 .621-.504 1.125-1.125 1.125h-5.25a1.125 1.125 0 01-1.125-1.125v-2.25z' });
    }

    if (props.canHumanize) {
        tabs.push({ key: 'humanize', label: 'Humanisation', icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z' });
    }

    return tabs;
});

watch(() => props.initialTab, (nextTab) => {
    if (availableTabs.value.some((tab) => tab.key === nextTab)) {
        activeTab.value = nextTab;
    }
}, { immediate: true });

watch(availableTabs, (tabs) => {
    if (!tabs.some((tab) => tab.key === activeTab.value)) {
        activeTab.value = tabs[0]?.key ?? 'overview';
    }
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
            badge: 'bg-rose-500/10 text-rose-700 dark:text-rose-300 ring-1 ring-rose-500/20',
            accent: 'text-rose-600 dark:text-rose-400',
            iconPath: 'M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z',
            iconColor: 'text-rose-600 dark:text-rose-400',
        };
    }

    if (value >= 60) {
        return {
            title: 'Probablement IA',
            subtitle: 'Le texte reste très structuré et présente plusieurs marqueurs typiques.',
            badge: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 ring-1 ring-amber-500/20',
            accent: 'text-amber-600 dark:text-amber-400',
            iconPath: 'M12 9v2.25m0 3h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
            iconColor: 'text-amber-600 dark:text-amber-400',
        };
    }

    if (value >= 30) {
        return {
            title: 'Incertain',
            subtitle: 'Le résultat mélange des indices humains et artificiels.',
            badge: 'bg-zinc-500/10 text-zinc-700 dark:text-zinc-300 ring-1 ring-zinc-500/20',
            accent: 'text-zinc-600 dark:text-zinc-400',
            iconPath: 'M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z',
            iconColor: 'text-zinc-600 dark:text-zinc-400',
        };
    }

    return {
        title: 'Très probablement humain',
        subtitle: 'Le document conserve une structure et une variation proches d\'un texte authentique.',
        badge: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 ring-1 ring-emerald-500/20',
        accent: 'text-emerald-600 dark:text-emerald-400',
        iconPath: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
        iconColor: 'text-emerald-600 dark:text-emerald-400',
    };
}

const verdict = computed(() => verdictMeta(props.result));

function authenticityBarColor(value) {
    const percent = normalizePercent(value);
    if (percent > 60) return 'bg-gradient-to-r from-emerald-500 to-teal-400';
    if (percent >= 40) return 'bg-gradient-to-r from-amber-400 to-orange-400';
    return 'bg-gradient-to-r from-rose-500 to-pink-500';
}

function sentenceClasses(score) {
    const value = normalizePercent(score);

    if (value >= 75) {
        return 'rounded-md border border-rose-300/60 bg-rose-500/15 px-1.5 py-0.5 text-zinc-800 transition-all duration-200 dark:border-rose-500/25 dark:bg-rose-500/20 dark:text-zinc-100 hover:bg-rose-500/25';
    }

    if (value >= 50) {
        return 'rounded-md border border-rose-200/50 bg-rose-500/8 px-1.5 py-0.5 text-zinc-800 transition-all duration-200 dark:border-rose-500/15 dark:bg-rose-500/12 dark:text-zinc-100 hover:bg-rose-500/15';
    }

    if (value >= 25) {
        return 'rounded-md border border-emerald-200/50 bg-emerald-500/8 px-1.5 py-0.5 text-zinc-800 transition-all duration-200 dark:border-emerald-500/12 dark:bg-emerald-500/8 dark:text-zinc-100 hover:bg-emerald-500/15';
    }

    return 'rounded-md border border-emerald-300/60 bg-emerald-500/15 px-1.5 py-0.5 text-zinc-800 transition-all duration-200 dark:border-emerald-500/20 dark:bg-emerald-500/15 dark:text-zinc-100 hover:bg-emerald-500/25';
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
    const subject = encodeURIComponent('Résultat d\'analyse ReinIA');
    const body = encodeURIComponent(`${shareText.value}\n\n${shareUrl.value}`);
    return `mailto:?subject=${subject}&body=${body}`;
});

async function copyShareText() {
    try {
        await navigator.clipboard.writeText(`${shareText.value} ${shareUrl.value}`.trim());
        copied.value = true;
        setTimeout(() => { copied.value = false; }, 2000);
    } catch {
        copied.value = false;
    }
}
</script>

<template>
    <div class="animate-slide-up space-y-6">
        <!-- Tab navigation -->
        <div class="border-b border-zinc-200/50 dark:border-zinc-800/50">
            <nav class="-mb-px flex items-center gap-1">
                <button
                    v-for="tab in availableTabs"
                    :key="tab.key"
                    type="button"
                    class="flex items-center gap-2 rounded-t-lg border-b-2 px-4 py-3 text-sm font-medium transition-all duration-200 cursor-pointer"
                    :class="activeTab === tab.key
                        ? 'border-indigo-500 text-zinc-900 dark:text-zinc-50'
                        : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200'"
                    @click="activeTab = tab.key"
                >
                    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" :d="tab.icon" /></svg>
                    {{ tab.label }}
                </button>
            </nav>
        </div>

        <!-- ═══ OVERVIEW TAB ═══ -->
        <div v-if="activeTab === 'overview'" class="space-y-6">
            <section class="overflow-hidden rounded-xl border border-zinc-200/60 bg-white shadow-sm dark:border-zinc-800/60 dark:bg-zinc-900/80">
                <div class="p-6 sm:p-8">
                    <div class="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
                        <!-- Left -->
                        <div class="space-y-6">
                            <!-- Verdict -->
                            <div class="space-y-3">
                                <p class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Résultat de détection</p>
                                <div class="flex items-center gap-3">
                                    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-50 dark:bg-zinc-800/50">
                                        <svg class="h-5 w-5" :class="verdict.iconColor" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                                            <path stroke-linecap="round" stroke-linejoin="round" :d="verdict.iconPath" />
                                        </svg>
                                    </span>
                                    <div class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium" :class="verdict.badge">
                                        {{ verdict.title }}
                                    </div>
                                </div>
                                <p class="max-w-2xl text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">{{ verdict.subtitle }}</p>
                            </div>

                            <!-- Score cards -->
                            <div class="grid gap-3 sm:grid-cols-3">
                                <div class="group rounded-xl border border-zinc-200/60 bg-zinc-50/50 p-4 transition-all duration-200 hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800/60 dark:bg-zinc-800/30 dark:hover:border-zinc-700">
                                    <p class="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Authenticité</p>
                                    <p class="mt-2 font-display text-2xl font-bold tabular-nums text-zinc-900 dark:text-zinc-50">{{ humanPercent }}<span class="text-sm font-normal text-zinc-400">%</span></p>
                                </div>
                                <div class="group rounded-xl border border-zinc-200/60 bg-zinc-50/50 p-4 transition-all duration-200 hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800/60 dark:bg-zinc-800/30 dark:hover:border-zinc-700">
                                    <p class="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Détection IA</p>
                                    <p class="mt-2 font-display text-2xl font-bold tabular-nums text-zinc-900 dark:text-zinc-50">{{ aiPercent }}<span class="text-sm font-normal text-zinc-400">%</span></p>
                                </div>
                                <div class="group rounded-xl border border-zinc-200/60 bg-zinc-50/50 p-4 transition-all duration-200 hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800/60 dark:bg-zinc-800/30 dark:hover:border-zinc-700">
                                    <p class="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Verdict</p>
                                    <p class="mt-2 text-sm font-semibold" :class="verdict.accent">{{ verdict.title }}</p>
                                </div>
                            </div>

                            <!-- Authenticity bar -->
                            <div class="space-y-2">
                                <div class="flex items-center justify-between text-xs">
                                    <span class="font-medium text-zinc-700 dark:text-zinc-300">Score d'authenticité</span>
                                    <span class="tabular-nums text-zinc-500 dark:text-zinc-400">{{ humanPercent }}%</span>
                                </div>
                                <div class="h-2.5 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                                    <div class="h-full rounded-full transition-all duration-1000 ease-out" :class="authenticityBarColor(humanScore)" :style="{ width: `${humanScore}%` }"></div>
                                </div>
                                <div class="flex items-center justify-between text-[11px] text-zinc-400 dark:text-zinc-500">
                                    <span>Faible</span>
                                    <span>Élevé</span>
                                </div>
                            </div>

                            <!-- Humanize CTA -->
                            <button
                                v-if="canHumanize"
                                type="button"
                                class="group flex w-full items-center justify-center gap-2.5 rounded-xl border-2 border-dashed border-purple-300 bg-purple-50 px-4 py-3 text-sm font-semibold text-purple-700 transition-all duration-200 hover:border-purple-400 hover:bg-purple-100 dark:border-purple-500/30 dark:bg-purple-500/10 dark:text-purple-300 dark:hover:border-purple-500/50 dark:hover:bg-purple-500/15 cursor-pointer"
                                @click="activeTab = 'humanize'"
                            >
                                <svg class="h-5 w-5 transition-transform duration-200 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" /></svg>
                                Humaniser ce texte
                                <svg class="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
                            </button>
                        </div>

                        <!-- Right — Gauge -->
                        <div class="flex flex-col items-center justify-center rounded-xl border border-zinc-200/60 bg-zinc-50/50 p-6 dark:border-zinc-800/60 dark:bg-zinc-800/30">
                            <ScoreGauge :score="humanScore" label="Authenticité" size="lg" :invert-colors="true" />
                            <p class="mt-5 text-center text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
                                Score agrégé combinant détection multi-modèle, perplexité et burstiness.
                            </p>

                            <!-- Share actions -->
                            <div class="mt-6 w-full space-y-2 border-t border-zinc-200/50 pt-5 dark:border-zinc-700/50">
                                <a :href="whatsappShareUrl" target="_blank" rel="noopener noreferrer" class="group flex items-center justify-between rounded-lg border border-zinc-200/60 bg-white px-3.5 py-2.5 text-xs font-medium text-zinc-600 transition hover:bg-zinc-50 dark:border-zinc-700/60 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700">
                                    <span class="flex items-center">
                                        <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                                        </svg>
                                        WhatsApp
                                    </span>
                                    <svg class="h-3.5 w-3.5 text-zinc-400 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                                    </svg>
                                </a>
                                <a :href="emailShareUrl" class="group flex items-center justify-between rounded-lg border border-zinc-200/60 bg-white px-3.5 py-2.5 text-xs font-medium text-zinc-600 transition hover:bg-zinc-50 dark:border-zinc-700/60 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700">
                                    <span class="flex items-center">
                                        <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                                        </svg>
                                        Email
                                    </span>
                                    <svg class="h-3.5 w-3.5 text-zinc-400 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                                    </svg>
                                </a>
                                <button type="button" class="flex w-full items-center justify-between rounded-lg border border-zinc-200/60 bg-white px-3.5 py-2.5 text-xs font-medium text-zinc-600 transition hover:bg-zinc-50 dark:border-zinc-700/60 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 cursor-pointer" @click="copyShareText">
                                    <span class="flex items-center" :class="copied ? 'text-emerald-600 dark:text-emerald-400' : ''">
                                        <svg v-if="copied" class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
                                        <svg v-else class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" /></svg>
                                        {{ copied ? 'Copié !' : 'Copier' }}
                                    </span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        <!-- ═══ PHRASES TAB ═══ -->
        <section v-if="activeTab === 'phrases' && displaySentences" class="overflow-hidden rounded-xl border border-zinc-200/60 bg-white shadow-sm dark:border-zinc-800/60 dark:bg-zinc-900/80">
            <div class="border-b border-zinc-100 bg-zinc-50/50 px-6 py-4 dark:border-zinc-800 dark:bg-zinc-800/30">
                <div class="flex items-center justify-between gap-3">
                    <div>
                        <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Détail phrase par phrase</h3>
                        <p class="mt-1 text-xs text-zinc-500 dark:text-zinc-400">Chaque phrase est colorée selon sa probabilité d'origine.</p>
                    </div>
                    <span class="rounded-full border border-zinc-200 bg-white px-2.5 py-0.5 text-xs font-medium tabular-nums text-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-400">{{ displaySentences.length }}</span>
                </div>
                <div class="mt-3 flex items-center gap-4 text-xs text-zinc-500 dark:text-zinc-400">
                    <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-sm border border-emerald-200 bg-emerald-500/15"></span> Humain</span>
                    <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-3 rounded-sm border border-rose-200 bg-rose-500/15"></span> IA</span>
                </div>
            </div>

            <div class="p-5 sm:p-6">
                <p class="text-sm leading-8 text-zinc-700 dark:text-zinc-200">
                    <template v-for="(sentence, index) in displaySentences" :key="sentence.id ?? index">
                        <span class="group relative inline-block align-baseline" :style="{ animationDelay: `${index * 30}ms` }">
                            <span :class="sentenceClasses(sentence.score)" :title="sentenceTooltip(sentence.score)">{{ sentence.text }}</span>
                            <span class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:bg-zinc-100 dark:text-zinc-900">
                                {{ sentenceTooltip(sentence.score) }}
                            </span>
                        </span>{{ ' ' }}
                    </template>
                </p>
            </div>
        </section>

        <!-- ═══ SECTIONS TAB ═══ -->
        <div v-if="activeTab === 'sections' && hasSections" class="space-y-4">
            <!-- Preprocessing stats -->
            <div v-if="preprocessing" class="rounded-xl border border-zinc-200/60 bg-white p-5 shadow-sm dark:border-zinc-800/60 dark:bg-zinc-900/80">
                <div class="grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
                    <div class="rounded-lg border border-zinc-200/50 bg-zinc-50/50 px-4 py-3 dark:border-zinc-800/50 dark:bg-zinc-800/30">
                        <p class="text-xs font-medium uppercase tracking-wider text-zinc-400 dark:text-zinc-500">Original</p>
                        <p class="mt-1 font-display font-bold text-zinc-900 dark:text-zinc-100">{{ (preprocessing.original_length / 1000).toFixed(1) }}k <span class="text-xs font-normal text-zinc-400">car.</span></p>
                    </div>
                    <div class="rounded-lg border border-zinc-200/50 bg-zinc-50/50 px-4 py-3 dark:border-zinc-800/50 dark:bg-zinc-800/30">
                        <p class="text-xs font-medium uppercase tracking-wider text-zinc-400 dark:text-zinc-500">Analysé</p>
                        <p class="mt-1 font-display font-bold text-zinc-900 dark:text-zinc-100">{{ (preprocessing.cleaned_length / 1000).toFixed(1) }}k <span class="text-xs font-normal text-zinc-400">car.</span></p>
                    </div>
                    <div class="rounded-lg border border-zinc-200/50 bg-zinc-50/50 px-4 py-3 dark:border-zinc-800/50 dark:bg-zinc-800/30">
                        <p class="text-xs font-medium uppercase tracking-wider text-zinc-400 dark:text-zinc-500">Filtré</p>
                        <p class="mt-1 font-display font-bold text-zinc-900 dark:text-zinc-100">{{ preprocessing.sections_removed || 0 }} <span class="text-xs font-normal text-zinc-400">sections</span></p>
                    </div>
                    <div class="rounded-lg border border-zinc-200/50 bg-zinc-50/50 px-4 py-3 dark:border-zinc-800/50 dark:bg-zinc-800/30">
                        <p class="text-xs font-medium uppercase tracking-wider text-zinc-400 dark:text-zinc-500">Chunks</p>
                        <p class="mt-1 font-display font-bold text-zinc-900 dark:text-zinc-100">{{ preprocessing.chunk_count || chunkResults.length }}</p>
                    </div>
                </div>
            </div>

            <!-- Section cards -->
            <div
                v-for="(chunk, index) in chunkResults"
                :key="index"
                class="overflow-hidden rounded-xl border border-zinc-200/60 bg-white shadow-sm transition-all duration-200 dark:border-zinc-800/60 dark:bg-zinc-900/80"
                :style="{ animationDelay: `${index * 50}ms` }"
            >
                <button
                    type="button"
                    class="flex w-full items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/40 cursor-pointer"
                    @click="toggleChunk(index)"
                >
                    <div class="flex-1">
                        <div class="flex flex-wrap items-center gap-2">
                            <p class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Section {{ index + 1 }}</p>
                            <span class="text-xs text-zinc-500 dark:text-zinc-400">{{ chunk.label }}</span>
                        </div>
                        <p class="mt-1 text-xs text-zinc-400 dark:text-zinc-500">{{ chunk.char_count?.toLocaleString() }} car.</p>
                    </div>

                    <div class="w-24">
                        <div class="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div class="h-full rounded-full transition-all duration-500" :class="authenticityBarColor(100 - normalizePercent(chunk.ai_probability))" :style="{ width: `${100 - normalizePercent(chunk.ai_probability)}%` }"></div>
                        </div>
                    </div>

                    <div class="text-right">
                        <p class="text-sm font-bold tabular-nums text-zinc-900 dark:text-zinc-100">{{ (100 - normalizePercent(chunk.ai_probability)).toFixed(1) }}%</p>
                        <p class="text-xs text-zinc-500 dark:text-zinc-400">{{ chunkVerdict(chunk.ai_probability) }}</p>
                    </div>

                    <svg class="h-4 w-4 shrink-0 text-zinc-400 transition-transform duration-200" :class="expandedChunks[index] ? 'rotate-180' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
                </button>

                <transition
                    enter-active-class="transition-all duration-300 ease-out"
                    enter-from-class="max-h-0 opacity-0"
                    enter-to-class="max-h-[2000px] opacity-100"
                    leave-active-class="transition-all duration-200 ease-in"
                    leave-from-class="max-h-[2000px] opacity-100"
                    leave-to-class="max-h-0 opacity-0"
                >
                    <div v-if="expandedChunks[index]" class="overflow-hidden border-t border-zinc-100 bg-zinc-50/50 px-5 py-5 dark:border-zinc-800 dark:bg-zinc-800/20">
                        <div class="mb-4 grid gap-3 sm:grid-cols-3">
                            <div class="rounded-lg border border-zinc-200/50 bg-white px-4 py-3 dark:border-zinc-700/50 dark:bg-zinc-800/60">
                                <p class="text-xs text-zinc-500 dark:text-zinc-400">RoBERTa</p>
                                <p class="mt-1 font-display font-bold text-zinc-900 dark:text-zinc-100">{{ ((chunk.score_roberta || 0) * 100).toFixed(1) }}%</p>
                            </div>
                            <div class="rounded-lg border border-zinc-200/50 bg-white px-4 py-3 dark:border-zinc-700/50 dark:bg-zinc-800/60">
                                <p class="text-xs text-zinc-500 dark:text-zinc-400">Perplexité</p>
                                <p class="mt-1 font-display font-bold text-zinc-900 dark:text-zinc-100">{{ ((chunk.score_ppl || 0) * 100).toFixed(1) }}%</p>
                            </div>
                            <div class="rounded-lg border border-zinc-200/50 bg-white px-4 py-3 dark:border-zinc-700/50 dark:bg-zinc-800/60">
                                <p class="text-xs text-zinc-500 dark:text-zinc-400">Détection IA</p>
                                <p class="mt-1 font-display font-bold text-zinc-900 dark:text-zinc-100">{{ normalizePercent(chunk.ai_probability).toFixed(1) }}%</p>
                            </div>
                        </div>

                        <div v-if="chunk.sentences?.length" class="rounded-lg border border-zinc-200/50 bg-white p-5 dark:border-zinc-700/50 dark:bg-zinc-800/60">
                            <p class="text-sm leading-8 text-zinc-700 dark:text-zinc-200">
                                <template v-for="(sentence, sentenceIndex) in chunk.sentences" :key="sentence.id ?? sentenceIndex">
                                    <span class="group relative inline-block align-baseline">
                                        <span :class="sentenceClasses(sentence.score)" :title="sentenceTooltip(sentence.score)">{{ sentence.text }}</span>
                                        <span class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:bg-zinc-100 dark:text-zinc-900">
                                            {{ sentenceTooltip(sentence.score) }}
                                        </span>
                                    </span>{{ ' ' }}
                                </template>
                            </p>
                        </div>
                        <p v-else class="whitespace-pre-line text-sm leading-7 text-zinc-600 dark:text-zinc-300">{{ chunk.text }}</p>
                    </div>
                </transition>
            </div>
        </div>

        <!-- ═══ HUMANIZE TAB ═══ -->
        <div v-if="activeTab === 'humanize'">
            <slot name="humanize"></slot>
        </div>
    </div>
</template>
