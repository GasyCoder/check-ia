<script setup>
import { computed, ref, watch } from 'vue';
import { Head } from '@inertiajs/vue3';
import axios from 'axios';

const text = ref('');
const result = ref(null);
const sentences = ref(null);
const error = ref(null);
const loading = ref(false);
const dark = ref(typeof window !== 'undefined' ? localStorage.getItem('theme') === 'dark' : false);
const resultsSection = ref(null);

const maxChars = 20000;
const minChars = 10;

const charCount = computed(() => text.value.length);
const canAnalyze = computed(() => !loading.value && text.value.trim().length >= minChars);
const currentYear = new Date().getFullYear();
const humanPercent = computed(() => (result.value !== null ? (100 - result.value).toFixed(1) : '0.0'));
const aiPercent = computed(() => (result.value !== null ? result.value.toFixed(1) : '0.0'));

const verdict = computed(() => {
    if (result.value === null) return '';
    if (result.value >= 75) return 'Signal IA élevé détecté.';
    if (result.value >= 50) return 'Texte partiellement généré.';
    if (result.value >= 25) return 'Signal mixte — relecture conseillée.';
    return 'Le texte paraît rédigé par un humain.';
});

function sentenceBg(score) {
    if (score >= 50) return 'bg-rose-200 dark:bg-rose-500/20';
    return 'bg-emerald-100 dark:bg-emerald-500/15';
}

function clearText() {
    text.value = '';
    result.value = null;
    sentences.value = null;
    error.value = null;
}

watch(
    dark,
    value => {
        document.documentElement.classList.toggle('dark', value);
        localStorage.setItem('theme', value ? 'dark' : 'light');
    },
    { immediate: true },
);

function toggleTheme() {
    dark.value = !dark.value;
}

async function analyze() {
    if (!canAnalyze.value) return;
    loading.value = true;
    result.value = null;
    sentences.value = null;
    error.value = null;

    try {
        const response = await axios.post('/guest/analyze-text', { text: text.value }, { timeout: 120000 });
        result.value = response.data.result;
        sentences.value = response.data.sentences || [];
        requestAnimationFrame(() => {
            resultsSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    } catch (err) {
        if (err.response?.status === 429) {
            error.value = 'Trop de requêtes. Réessayez dans une minute.';
        } else {
            error.value = err.response?.data?.error || "Une erreur est survenue pendant l'analyse.";
        }
    } finally {
        loading.value = false;
    }
}

function scrollToAnalyse() {
    document.getElementById('analyse')?.scrollIntoView({ behavior: 'smooth' });
}
</script>

<template>
    <Head title="ReinIA — Détecteur de texte IA" />

    <div class="min-h-screen bg-white text-zinc-900 transition-colors dark:bg-zinc-950 dark:text-zinc-100" style="font-family: Inter, ui-sans-serif, system-ui, sans-serif;">

        <!-- Navbar -->
        <nav class="sticky top-0 z-50 border-b border-zinc-200 bg-white/80 backdrop-blur-xl dark:border-zinc-800 dark:bg-zinc-950/80">
            <div class="mx-auto flex max-w-6xl items-center justify-between px-5 py-3 sm:px-8">
                <a href="/" class="flex items-center gap-2.5">
                    <span class="flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900">
                        <span class="h-3 w-3 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.4)]"></span>
                    </span>
                    <span class="text-[15px] font-semibold tracking-tight">ReinIA</span>
                </a>

                <div class="flex items-center gap-1 sm:gap-2">
                    <a href="#tarifs" class="hidden px-3 py-2 text-sm text-zinc-500 transition hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white sm:inline-flex">Tarifs</a>
                    <button
                        type="button"
                        class="inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg border border-zinc-200 text-zinc-500 transition hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-900"
                        @click="toggleTheme"
                    >
                        <svg v-if="dark" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1.5m0 15V21m9-9h-1.5m-15 0H3m15.364 6.364l-1.06-1.06M6.696 6.696l-1.06-1.06m12.728 0l-1.06 1.06M6.696 17.304l-1.06 1.06M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
                        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" /></svg>
                    </button>
                    <a href="/login" class="hidden rounded-lg px-3 py-2 text-sm text-zinc-600 transition hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white sm:inline-flex">Se connecter</a>
                    <a href="/register" class="rounded-lg bg-zinc-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white">Commencer</a>
                </div>
            </div>
        </nav>

        <main>
            <!-- Hero -->
            <section class="mx-auto max-w-6xl px-5 pt-20 pb-16 text-center sm:px-8 sm:pt-28 sm:pb-20">
                <div class="mx-auto max-w-3xl">
                    <p class="text-sm font-medium uppercase tracking-widest text-zinc-400 dark:text-zinc-500">Plateforme de detection IA</p>
                    <h1 class="mt-5 text-4xl font-bold tracking-tight text-zinc-950 dark:text-white sm:text-5xl lg:text-[3.5rem] lg:leading-[1.15]">
                        Détectez l'IA avec une<br class="hidden sm:block" /> précision chirurgicale.
                    </h1>
                    <p class="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-zinc-500 dark:text-zinc-400">
                        La solution locale et confidentielle pour les institutions académiques et les créateurs de contenu.
                    </p>

                    <div class="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
                        <button @click="scrollToAnalyse" class="cursor-pointer rounded-lg bg-zinc-950 px-7 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white">
                            Commencer gratuitement
                        </button>
                        <a href="#methode" class="rounded-lg border border-zinc-200 bg-white px-7 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800">
                            Voir la méthode
                        </a>
                    </div>

                    <p class="mt-6 text-sm text-zinc-400 dark:text-zinc-500">
                        Utilisé par <span class="font-medium text-zinc-600 dark:text-zinc-300">+500 utilisateurs</span> à Mahajanga
                    </p>
                </div>
            </section>

            <!-- Feature grid -->
            <section id="methode" class="border-t border-zinc-100 bg-zinc-50/50 py-16 dark:border-zinc-800 dark:bg-zinc-900/30 sm:py-20">
                <div class="mx-auto max-w-6xl px-5 sm:px-8">
                    <p class="text-sm font-medium uppercase tracking-widest text-zinc-400 dark:text-zinc-500">Pourquoi ReinIA</p>
                    <h2 class="mt-3 text-2xl font-bold tracking-tight text-zinc-950 dark:text-white sm:text-3xl">Trois piliers, un score fiable.</h2>

                    <div class="mt-10 grid gap-px overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-200 dark:border-zinc-800 dark:bg-zinc-800 sm:grid-cols-3">
                        <!-- Feature 1 -->
                        <div class="bg-white p-7 dark:bg-zinc-950">
                            <div class="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 dark:border-zinc-700">
                                <svg class="h-5 w-5 text-zinc-600 dark:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
                            </div>
                            <h3 class="mt-4 text-[15px] font-semibold text-zinc-900 dark:text-white">Confidentialité Totale</h3>
                            <p class="mt-2 text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">Analyse 100% locale. Aucune donnée ne quitte votre serveur. Conforme RGPD.</p>
                        </div>
                        <!-- Feature 2 -->
                        <div class="bg-white p-7 dark:bg-zinc-950">
                            <div class="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 dark:border-zinc-700">
                                <svg class="h-5 w-5 text-zinc-600 dark:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" /></svg>
                            </div>
                            <h3 class="mt-4 text-[15px] font-semibold text-zinc-900 dark:text-white">Analyse Hybride</h3>
                            <p class="mt-2 text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">RoBERTa + Perplexité GPT-2 + Burstiness. Trois modèles pour contrer GPT-4o, Claude et Gemini.</p>
                        </div>
                        <!-- Feature 3 -->
                        <div class="bg-white p-7 dark:bg-zinc-950">
                            <div class="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 dark:border-zinc-700">
                                <svg class="h-5 w-5 text-zinc-600 dark:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                            </div>
                            <h3 class="mt-4 text-[15px] font-semibold text-zinc-900 dark:text-white">Rapports Détaillés</h3>
                            <p class="mt-2 text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">Coloration phrase par phrase, scores par section, export et historique complet.</p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Guest analysis -->
            <section id="analyse" class="border-t border-zinc-100 py-16 dark:border-zinc-800 sm:py-20">
                <div class="mx-auto max-w-3xl px-5 sm:px-8">
                    <div class="text-center">
                        <p class="text-sm font-medium uppercase tracking-widest text-zinc-400 dark:text-zinc-500">Essayer maintenant</p>
                        <h2 class="mt-3 text-2xl font-bold tracking-tight text-zinc-950 dark:text-white sm:text-3xl">Testez gratuitement</h2>
                        <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">Jusqu'à 20 000 caractères, sans inscription.</p>
                    </div>

                    <div class="mt-8 overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
                        <textarea
                            v-model="text"
                            rows="8"
                            :maxlength="maxChars"
                            placeholder="Collez votre texte ici pour l'analyser..."
                            class="w-full resize-none border-0 bg-transparent px-5 py-5 text-[15px] leading-7 text-zinc-800 outline-none placeholder:text-zinc-300 dark:text-zinc-200 dark:placeholder:text-zinc-600"
                        ></textarea>
                        <div class="flex items-center justify-between border-t border-zinc-100 px-5 py-3 dark:border-zinc-800">
                            <div class="flex items-center gap-3">
                                <span class="text-xs tabular-nums text-zinc-400 dark:text-zinc-500">{{ charCount.toLocaleString() }} / {{ maxChars.toLocaleString() }}</span>
                                <button v-if="text" @click="clearText" class="cursor-pointer text-xs text-zinc-400 transition hover:text-zinc-600 dark:hover:text-zinc-300">Effacer</button>
                            </div>
                            <button
                                @click="analyze"
                                :disabled="!canAnalyze"
                                class="cursor-pointer rounded-lg bg-zinc-950 px-5 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-400 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white dark:disabled:bg-zinc-800 dark:disabled:text-zinc-500"
                            >
                                <span v-if="loading" class="flex items-center gap-2">
                                    <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                                    Analyse...
                                </span>
                                <span v-else>Analyser</span>
                            </button>
                        </div>
                    </div>

                    <div v-if="error" class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
                        {{ error }}
                    </div>

                    <!-- Result -->
                    <div v-if="result !== null" ref="resultsSection" class="mt-6 space-y-4">
                        <div class="rounded-2xl border border-zinc-200 bg-zinc-50 p-6 dark:border-zinc-800 dark:bg-zinc-900">
                            <div class="flex flex-col items-center gap-5 sm:flex-row sm:justify-between">
                                <div>
                                    <p class="text-xs font-medium uppercase tracking-wide text-zinc-400 dark:text-zinc-500">Résultat</p>
                                    <p class="mt-1 text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ verdict }}</p>
                                </div>
                                <div class="flex gap-4 text-center">
                                    <div class="rounded-xl bg-white px-5 py-3 dark:bg-zinc-950">
                                        <p class="text-xs text-zinc-400">Humain</p>
                                        <p class="mt-1 text-2xl font-bold tabular-nums text-emerald-600">{{ humanPercent }}%</p>
                                    </div>
                                    <div class="rounded-xl bg-white px-5 py-3 dark:bg-zinc-950">
                                        <p class="text-xs text-zinc-400">IA</p>
                                        <p class="mt-1 text-2xl font-bold tabular-nums text-red-600">{{ aiPercent }}%</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div v-if="sentences && sentences.length" class="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
                            <p class="text-sm font-medium text-zinc-700 dark:text-zinc-300">Détail phrase par phrase</p>
                            <p class="mt-3 text-sm leading-8 text-zinc-700 dark:text-zinc-300">
                                <template v-for="(s, i) in sentences" :key="i">
                                    <span class="rounded px-0.5 py-0.5" :class="sentenceBg(s.score)" :title="`Score IA : ${s.score}%`">{{ s.text }}</span>{{ ' ' }}
                                </template>
                            </p>
                        </div>

                        <div class="rounded-xl border border-zinc-200 bg-zinc-50 px-5 py-4 dark:border-zinc-800 dark:bg-zinc-900">
                            <div class="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
                                <p class="text-sm text-zinc-500 dark:text-zinc-400">Analyse complète ? Fichiers PDF, historique et sections détaillées.</p>
                                <a href="/register" class="shrink-0 rounded-lg bg-zinc-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white">Créer un compte</a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Pricing -->
            <section id="tarifs" class="border-t border-zinc-100 bg-zinc-50/50 py-16 dark:border-zinc-800 dark:bg-zinc-900/30 sm:py-20">
                <div class="mx-auto max-w-6xl px-5 sm:px-8">
                    <div class="text-center">
                        <p class="text-sm font-medium uppercase tracking-widest text-zinc-400 dark:text-zinc-500">Tarifs</p>
                        <h2 class="mt-3 text-2xl font-bold tracking-tight text-zinc-950 dark:text-white sm:text-3xl">Un plan pour chaque besoin.</h2>
                        <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">Commencez gratuitement, évoluez quand vous le souhaitez.</p>
                    </div>

                    <div class="mt-12 grid gap-6 sm:grid-cols-3">
                        <!-- Gratuit -->
                        <div class="flex flex-col rounded-2xl border border-zinc-200 bg-white p-7 dark:border-zinc-800 dark:bg-zinc-950">
                            <p class="text-sm font-semibold text-zinc-900 dark:text-white">Gratuit</p>
                            <p class="mt-3"><span class="text-3xl font-bold text-zinc-950 dark:text-white">0</span> <span class="text-sm text-zinc-400">Ar/mois</span></p>
                            <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">Pour découvrir et tester l'outil.</p>
                            <ul class="mt-6 flex-1 space-y-3 text-sm text-zinc-600 dark:text-zinc-400">
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>5 analyses / jour</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>20 000 caractères max</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Coloration par phrase</li>
                            </ul>
                            <button @click="scrollToAnalyse" class="mt-8 w-full cursor-pointer rounded-lg border border-zinc-200 bg-white py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800">
                                Essayer maintenant
                            </button>
                        </div>

                        <!-- Pro -->
                        <div class="relative flex flex-col rounded-2xl border-2 border-zinc-950 bg-white p-7 shadow-lg dark:border-zinc-100 dark:bg-zinc-950">
                            <span class="absolute -top-3 left-6 rounded-full bg-zinc-950 px-3 py-1 text-xs font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900">Populaire</span>
                            <p class="text-sm font-semibold text-zinc-900 dark:text-white">Pro</p>
                            <p class="mt-3"><span class="text-3xl font-bold text-zinc-950 dark:text-white">25 000</span> <span class="text-sm text-zinc-400">Ar/mois</span></p>
                            <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">Pour les professionnels et enseignants.</p>
                            <ul class="mt-6 flex-1 space-y-3 text-sm text-zinc-600 dark:text-zinc-400">
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-950 dark:text-zinc-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg><span class="font-medium text-zinc-900 dark:text-white">Analyses illimitées</span></li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-950 dark:text-zinc-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>1 500 000 caractères</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-950 dark:text-zinc-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Import PDF / DOCX</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-950 dark:text-zinc-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Historique + Export</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-950 dark:text-zinc-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Support prioritaire</li>
                            </ul>
                            <a href="/register" class="mt-8 block w-full rounded-lg bg-zinc-950 py-2.5 text-center text-sm font-medium text-white transition hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white">
                                S'abonner
                            </a>
                        </div>

                        <!-- Institution -->
                        <div class="flex flex-col rounded-2xl border border-zinc-200 bg-white p-7 dark:border-zinc-800 dark:bg-zinc-950">
                            <p class="text-sm font-semibold text-zinc-900 dark:text-white">Institution</p>
                            <p class="mt-3"><span class="text-3xl font-bold text-zinc-950 dark:text-white">Sur devis</span></p>
                            <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">Installation on-premise pour Universités.</p>
                            <ul class="mt-6 flex-1 space-y-3 text-sm text-zinc-600 dark:text-zinc-400">
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Tout du plan Pro</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Déploiement sur votre serveur</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Multi-utilisateurs + Rôles</li>
                                <li class="flex items-start gap-2.5"><svg class="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>Formation + Support dédié</li>
                            </ul>
                            <a href="mailto:contact@reinia.mg" class="mt-8 block w-full rounded-lg border border-zinc-200 bg-white py-2.5 text-center text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800">
                                Nous contacter
                            </a>
                        </div>
                    </div>
                </div>
            </section>

            <!-- CTA final -->
            <section class="border-t border-zinc-100 py-16 dark:border-zinc-800 sm:py-20">
                <div class="mx-auto max-w-2xl px-5 text-center sm:px-8">
                    <h2 class="text-2xl font-bold tracking-tight text-zinc-950 dark:text-white sm:text-3xl">Prêt à détecter ?</h2>
                    <p class="mt-3 text-sm text-zinc-500 dark:text-zinc-400">Créez votre compte en 30 secondes. Aucune carte bancaire requise.</p>
                    <div class="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
                        <a href="/register" class="rounded-lg bg-zinc-950 px-7 py-3 text-sm font-semibold text-white transition hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white">Créer un compte gratuit</a>
                        <a href="/auth/google" class="flex items-center gap-2.5 rounded-lg border border-zinc-200 bg-white px-6 py-3 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800">
                            <svg class="h-4 w-4" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                            Continuer avec Google
                        </a>
                    </div>
                </div>
            </section>
        </main>

        <!-- Footer -->
        <footer class="border-t border-zinc-200 dark:border-zinc-800">
            <div class="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-8 text-sm text-zinc-400 dark:text-zinc-500 sm:flex-row sm:items-center sm:justify-between sm:px-8">
                <div class="flex items-center gap-2">
                    <span class="flex h-6 w-6 items-center justify-center rounded border border-zinc-200 dark:border-zinc-700">
                        <span class="h-2 w-2 rounded-full bg-zinc-400"></span>
                    </span>
                    <span>&copy; {{ currentYear }} ReinIA</span>
                </div>
                <p>Analyse locale. Aucune donnée envoyée à des tiers.</p>
            </div>
        </footer>
    </div>
</template>
